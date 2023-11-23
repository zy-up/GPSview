from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button

class MyBoxLayout(BoxLayout):
    def __init__(self, **kwargs):
        super(MyBoxLayout, self).__init__(**kwargs)
        self.orientation = 'vertical'

        # 下拉菜单
        self.spinner = Spinner(
            text='9',
            values=('1', '2', '3', '4', '5'),
            size_hint=(None, None),
            size=(100, 44)
        )
        self.add_widget(self.spinner)

        # 输入框
        self.input = TextInput(
            text='0',
            multiline=False,
            size_hint=(None, None),
            size=(200, 44)
        )
        self.add_widget(self.input)

        # 按钮
        self.button = Button(
            text='start/stop',
            size_hint=(None, None),
            size=(200, 44)
        )
        self.button.bind(on_press=self.on_button_click)
        self.add_widget(self.button)

        # 复选框和标签
        self.check_add = CheckBox(group='operation')
        self.check_mul = CheckBox(group='operation')
        self.check_sub = CheckBox(group='operation')
        self.add_widget(Label(text='+'))
        self.add_widget(self.check_add)
        self.add_widget(Label(text='*'))
        self.add_widget(self.check_mul)
        self.add_widget(Label(text='-'))
        self.add_widget(self.check_sub)

        # 结果标签
        self.result_label = Label(text='result:')
        self.add_widget(self.result_label)

    def on_button_click(self, instance):
        initial_value = float(self.input.text)
        operation_value = int(self.spinner.text)
        result = initial_value

        if self.check_add.active:
            result += operation_value
        elif self.check_mul.active:
            result *= operation_value
        elif self.check_sub.active:
            result -= operation_value

        self.result_label.text = f'result: {result}'

class MyApp(App):
    def build(self):
        return MyBoxLayout()

if __name__ == '__main__':
    MyApp().run()
