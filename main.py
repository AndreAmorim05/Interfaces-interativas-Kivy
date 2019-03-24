import kivy
kivy.require('1.4.2')
import os
import sys
from kivy.app import App
from kivy.factory import Factory
from kivy.lang import Builder, Parser, ParserException
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.codeinput import CodeInput
from kivy.properties import ObjectProperty
from kivy.clock import Clock
from kivy.animation import Animation

# pega o path deste aquivo
CATALOG_ROOT = os.path.dirname(__file__)
# pega o caminho (path) da pasta que contem as telas em .kv
CONTAINER_KVS = os.path.join(CATALOG_ROOT, 'telas_kv')
# pega o nome dos arquivos sem a extenção .kv na pasta telas_kv
CONTAINER_CLASSES = [c[:-3] for c in os.listdir(CONTAINER_KVS)
        if c.endswith('.kv')]

class Container(BoxLayout):
    '''Um container é essencialmente uma classe que carrega a raiz
    de um arquivo .kv conhecido.

    O nome do arquivo .kv é levado da classe Container.
    Nós não podemos utilizar as regras kv porque a classe precisa
    ser editada na interface e recarregada pelo usuário.
    '''
    def __init__(self, **kwargs):
        super(Container, self).__init__(**kwargs)
        self.previous_text = open(self.kv_file).read()
        parser = Parser(content=self.previous_text)
        print(parser)
        widget = Factory.get(parser.root.name)()
        Builder._apply_rule(widget, parser.root, parser.root)
        self.add_widget(widget)

    @property
    def kv_file(self):
        '''Pega o nome do arquivo kv, uma versão caixa-baixa do nome
        da classe '''
        return os.path.join(CONTAINER_KVS,self.__class__.__name__ + '.kv')

for class_name in CONTAINER_CLASSES:
    globals()[class_name] = type(class_name, (Container,), {})

class IDERender(CodeInput):
    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        is_osx = sys.platform == 'darwin'
        # keycodes no is_osx
        ctrl, cmd = 64, 1024
        key, key_str = keycode

        if text and key not in (list(self.interesting_keys.keys())+[27]):
            # isto permite ctrl ou cmd, mas não ambos
            if modifiers == ['ctrl'] or (is_osx and modifiers == ['meta']):
                if key == ord('s'):
                    self.catalog.change_kv(True)
                    return

        return super(IDERender, self).keyboard_on_key_down(
            window, keycode, text, modifiers)

class Catalog(BoxLayout):
    # armazena os códigos que serão apresentados no editor de texto
    language_box = ObjectProperty()
    # gerancia as telas (screens) do projeto
    screen_manager = ObjectProperty()
    # armazena um Clock para atualizar automaticamente a interface
    _change_kv_ev = None

    def __init__(self, **kwargs):
        self._previously_parsed_text = ''
        super(Catalog, self).__init__(**kwargs)
        self.show_kv(None, 'Tela1')
        self.carousel = None

    def show_kv(self, instance, value):
        '''Chamada quando um item é selecionado, nós precisamos mostrar
        o arquivo com código .kv associado ao container recem revelado.'''

        self.screen_manager.current = value

        child = self.screen_manager.current_screen.children[0]
        with  open(child.kv_file, 'rb') as file:
            self.language_box.text = file.read().decode('utf8')
        if self._change_kv_ev is not None:
            self._change_kv_ev.cancel()
        self.change_kv()
        #  reseta o histórico do undo/redo
        self.language_box.reset_undo()

    def schedule_reload(self):
        if self.auto_reload:
            txt = self.language_box.text
            child = self.screen_manager.current_screen.children[0]
            if txt == child.previous_text:
                return
            child.previous_text = txt
            if self._change_kv_ev is not None:
                self._change_kv_ev.cancel()
            if self._change_kv_ev is None:
                self._change_kv_ev = Clock.create_trigger(self.change_kv, 2)
            self._change_kv_ev()

    def change_kv(self, *args):
        '''Chamado quando o botão de update é clicado. Precisa realizar
        o updare da interface para o o widget ativo no momento, se houver
        algum baseado no que o usuário digitou. Se houver um erro na
        sintaxe kv deles, mostra um popup legal.'''

        txt = self.language_box.text
        kv_container = self.screen_manager.current_screen.children[0]
        try:
            parser = Parser(content=txt)
            kv_container.clear_widgets()
            widget = Factory.get(parser.root.name)()
            Builder._apply_rule(widget, parser.root, parser.root)
            kv_container.add_widget(widget)
        except (SyntaxError, ParserException) as e:
            self.show_error(e)
        except Exception as e:
            self.show_error(e)

    def show_error(self, e):
        self.info_label.text = str(e).encode('utf8')
        self.anim = Animation(top=190.0, opacity=1, d=2, t='in_back') +\
            Animation(top=190.0, d=3) +\
            Animation(top=0, opacity=0, d=2)
        self.anim.start(self.info_label)

class InterfaceInterativaApp(App):

    def build(self):
        return Catalog()

    def on_pause(self):
        return True

if __name__ == '__main__':
    InterfaceInterativaApp().run()
