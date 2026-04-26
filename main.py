import json
import os
from collections import defaultdict
from functools import partial
from datetime import datetime

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup

# PDF (reportlab)
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm

# Compartilhar (Android)
from jnius import autoclass

ARQUIVO = "lancamentos.json"

def carregar():
    try:
        with open(ARQUIVO, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def salvar(lancamentos):
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(lancamentos, f, indent=2, ensure_ascii=False)

class Tela(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=10, padding=10, **kwargs)

        self.lancamentos = carregar()
        self.selecionado = None

        # Título
        self.add_widget(Label(text="📋 Controle de Diárias", size_hint_y=None, height=40, font_size=20, bold=True))

        # Caixas de entrada
        self.data = TextInput(hint_text="Data (AAAA-MM-DD)", multiline=False, size_hint_y=None, height=50)
        self.pessoa = TextInput(hint_text="Nome", multiline=False, size_hint_y=None, height=50)
        self.dias = TextInput(hint_text="Dias (1 ou 0.5)", multiline=False, size_hint_y=None, height=50)
        self.diaria = TextInput(hint_text="Valor diária", text="70", multiline=False, size_hint_y=None, height=50)

        self.dias.bind(text=self.calcular_valor)
        self.diaria.bind(text=self.calcular_valor)

        self.add_widget(self.data)
        self.add_widget(self.pessoa)
        self.add_widget(self.dias)
        self.add_widget(self.diaria)

        # Mostra valor calculado
        self.valor_label = Label(text="R$ 0.00", size_hint_y=None, height=40, font_size=18, color=(0,0.6,0,1))
        self.add_widget(self.valor_label)

        # Botões principais
        botoes = GridLayout(cols=2, spacing=10, size_hint_y=None, height=200)
        btn_add = Button(text="Adicionar", background_color=(0,0.6,0,1))
        btn_del = Button(text="Apagar", background_color=(0.8,0,0,1))
        btn_resumo = Button(text="Resumo", background_color=(0.2,0.4,1,1))
        btn_rank = Button(text="Ranking", background_color=(1,0.5,0,1))
        btn_pdf = Button(text="Recibo 58mm", background_color=(0.5,0,0.5,1))

        btn_add.bind(on_press=self.adicionar)
        btn_del.bind(on_press=self.apagar)
        btn_resumo.bind(on_press=self.resumo)
        btn_rank.bind(on_press=self.ranking)
        btn_pdf.bind(on_press=self.gerar_pdf_58mm)

        botoes.add_widget(btn_add)
        botoes.add_widget(btn_del)
        botoes.add_widget(btn_resumo)
        botoes.add_widget(btn_rank)
        botoes.add_widget(btn_pdf)
        self.add_widget(botoes)

        # Total geral
        self.total_label = Label(text="TOTAL: R$ 0.00", size_hint_y=None, height=40, bold=True)
        self.add_widget(self.total_label)

        # Lista rolável
        self.scroll = ScrollView()
        self.lista = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.lista.bind(minimum_height=self.lista.setter('height'))
        self.scroll.add_widget(self.lista)
        self.add_widget(self.scroll)

        self.atualizar_lista()
        self.atualizar_total()

    def atualizar_lista(self):
        self.lista.clear_widgets()
        for i, l in enumerate(self.lancamentos):
            valor = l["dias"] * l.get("diaria", 70)
            texto = f"{l['data']} | {l['pessoa']} | {l['dias']}d | R$ {valor:.2f}"
            btn = Button(text=texto, size_hint_y=None, height=50,
                         background_color=(0.9,0.9,0.9,1), color=(0,0,0,1))
            btn.bind(on_press=partial(self.selecionar, i))
            self.lista.add_widget(btn)

    def selecionar(self, index, *args):
        self.selecionado = index
        l = self.lancamentos[index]
        self.data.text = l["data"]
        self.pessoa.text = l["pessoa"]
        self.dias.text = str(l["dias"])
        self.diaria.text = str(l.get("diaria", 70))

    def adicionar(self, instance):
        try:
            dias = float(self.dias.text)
            diaria = float(self.diaria.text)
            self.lancamentos.append({
                "data": self.data.text,
                "pessoa": self.pessoa.text.lower(),
                "dias": dias,
                "diaria": diaria
            })
            salvar(self.lancamentos)
            self.atualizar_lista()
            self.atualizar_total()
            self.data.text = ""
            self.pessoa.text = ""
            self.dias.text = ""
        except:
            self.popup("Erro: verifique Dias e Diária (números)")

    def apagar(self, instance):
        if self.selecionado is not None:
            self.lancamentos.pop(self.selecionado)
            salvar(self.lancamentos)
            self.selecionado = None
            self.atualizar_lista()
            self.atualizar_total()

    def atualizar_total(self):
        total = sum(l["dias"] * l.get("diaria", 70) for l in self.lancamentos)
        self.total_label.text = f"TOTAL: R$ {total:.2f}"

    def calcular_valor(self, instance, value):
        try:
            dias = float(self.dias.text) if self.dias.text else 0
            diaria = float(self.diaria.text) if self.diaria.text else 0
            self.valor_label.text = f"R$ {dias * diaria:.2f}"
        except:
            self.valor_label.text = "R$ 0.00"

    def resumo(self, instance):
        totais = defaultdict(float)
        for l in self.lancamentos:
            totais[l["pessoa"]] += l["dias"]
        texto = "📊 RESUMO\n\n"
        for p, d in sorted(totais.items()):
            valor = sum(l["dias"] * l.get("diaria",70) for l in self.lancamentos if l["pessoa"] == p)
            texto += f"{p}: {d} dias → R$ {valor:.2f}\n"
        self.popup(texto)

    def ranking(self, instance):
        totais = {}
        for l in self.lancamentos:
            totais[l["pessoa"]] = totais.get(l["pessoa"],0) + l["dias"]
        ranking = []
        for p in totais:
            valor = sum(l["dias"] * l.get("diaria",70) for l in self.lancamentos if l["pessoa"] == p)
            ranking.append((p, valor, totais[p]))
        ranking.sort(key=lambda x: x[1], reverse=True)
        texto = "🏆 RANKING\n\n"
        for i,(p,v,d) in enumerate(ranking):
            medalha = ["🥇","🥈","🥉"][i] if i<3 else f"{i+1}º"
            texto += f"{medalha} {p}: R$ {v:.2f} ({d} dias)\n"
        self.popup(texto)

    def gerar_pdf_58mm(self, instance):
        if not self.lancamentos:
            self.popup("Nenhum lançamento para gerar recibo.")
            return

        try:
            # Caminho no Android (Downloads) ou na pasta atual
            if os.path.exists("/storage/emulated/0/Download"):
                caminho = "/storage/emulated/0/Download/recibo_58mm.pdf"
            else:
                caminho = "recibo_58mm.pdf"

            # Dimensões para papel térmica 58mm
            LARGURA = 58 * mm
            # Altura adaptável (quanto mais lançamentos, maior)
            ALTURA = 100 * mm + (len(self.lancamentos) * 6 * mm)

            doc = SimpleDocTemplate(caminho, pagesize=(LARGURA, ALTURA),
                                    leftMargin=3*mm, rightMargin=3*mm,
                                    topMargin=5*mm, bottomMargin=5*mm)

            styles = getSampleStyleSheet()
            estilo_normal = styles['Normal']
            estilo_normal.fontSize = 8
            estilo_centralizado = ParagraphStyle('Centralizado', parent=styles['Normal'], alignment=1, fontSize=10)

            elementos = []

            # Título
            elementos.append(Paragraph("<b>RECIBO DE PAGAMENTO</b>", estilo_centralizado))
            elementos.append(Paragraph("Diárias de serviço", estilo_centralizado))
            elementos.append(Spacer(1, 5))
            elementos.append(Paragraph("_" * 30, estilo_normal))
            elementos.append(Spacer(1, 5))

            # Data de emissão
            elementos.append(Paragraph(f"Emissão: {datetime.now().strftime('%d/%m/%Y %H:%M')}", estilo_normal))
            elementos.append(Spacer(1, 8))

            # Tabela simbólica (cabeçalho)
            elementos.append(Paragraph("<b>Data   Benef   Dias  Valor</b>", estilo_normal))
            total = 0
            for l in self.lancamentos:
                diaria = l.get("diaria", 70)
                valor = l["dias"] * diaria
                total += valor
                linha = f"{l['data']}  {l['pessoa'][:8]}   {l['dias']}    R$ {valor:.2f}"
                elementos.append(Paragraph(linha, estilo_normal))

            elementos.append(Spacer(1, 10))
            elementos.append(Paragraph(f"<b>TOTAL: R$ {total:.2f}</b>", estilo_centralizado))
            elementos.append(Spacer(1, 20))
            elementos.append(Paragraph("_________________________", estilo_centralizado))
            elementos.append(Paragraph("Assinatura", estilo_centralizado))
            elementos.append(Paragraph("* Comprovante de diárias *", estilo_centralizado))

            doc.build(elementos)
            self.popup(f"✅ Recibo gerado!\n{caminho}")
            self.compartilhar_pdf(caminho)

        except Exception as e:
            self.popup(f"Erro ao gerar PDF: {str(e)}")

    def compartilhar_pdf(self, caminho):
        try:
            Intent = autoclass('android.content.Intent')
            Uri = autoclass('android.net.Uri')
            File = autoclass('java.io.File')
            intent = Intent(Intent.ACTION_SEND)
            intent.setType("application/pdf")
            uri = Uri.fromFile(File(caminho))
            intent.putExtra(Intent.EXTRA_STREAM, uri)
            activity = autoclass('org.kivy.android.PythonActivity').mActivity
            activity.startActivity(Intent.createChooser(intent, "Compartilhar Recibo"))
        except:
            pass  # Se falhar (ex: não for Android), apenas ignora

    def popup(self, texto):
        box = BoxLayout(orientation='vertical')
        box.add_widget(Label(text=texto))
        btn = Button(text="Fechar", size_hint_y=None, height=50)
        box.add_widget(btn)
        popup = Popup(title="Info", content=box, size_hint=(0.9,0.5))
        btn.bind(on_press=popup.dismiss)
        popup.open()

class MeuApp(App):
    def build(self):
        return Tela()

if __name__ == "__main__":
    MeuApp().run()
