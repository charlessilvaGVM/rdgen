"""GVM Suporte - ajustes no código do cliente (RustDesk 1.4.9) antes de compilar o Windows (20/10/2026).

Uso no workflow: python gvm/patch_cliente.py <pasta do rustdesk>
Cada troca precisa casar exatamente uma vez; se o código do RustDesk mudar, o build falha aqui.
  1. "Desenvolvido por GVM Sistemas" (loadPowered) abre gvmsistemas.com.br, e não rustdesk.com
  2. tela Instalar: link do contrato de licença -> gvmsistemas.com.br
  3. Aplicativos instalados do Windows (MSI): links de ajuda/contato -> gvmsistemas.com.br
  4. Catálogo: a observação (nota) aparece embaixo do nome do card, legível, em até 2 linhas
     (sai da parte colorida); card do Catálogo com nota fica com 172 px de altura (os outros, 140)
  5. "Editar anotação": janela de 900 px, caixa de 12 linhas com rolagem, Enter = nova linha, até 2000 caracteres
"""
import os
import sys

SITE = "https://gvmsistemas.com.br"
RAIZ = sys.argv[1] if len(sys.argv) > 1 else "."


def trocar(arquivo, antigo, novo, vezes=1):
    caminho = os.path.join(RAIZ, arquivo)
    with open(caminho, encoding="utf-8") as f:
        texto = f.read()
    if "\r\n" in texto:  # checkout no runner Windows pode vir com CRLF
        antigo, novo = antigo.replace("\n", "\r\n"), novo.replace("\n", "\r\n")
    achou = texto.count(antigo)
    if achou != vezes:
        sys.exit(f"::error::GVM: {arquivo}: esperado {vezes}x, achado {achou}x: {antigo[:80]!r}")
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        f.write(texto.replace(antigo, novo))
    print(f"GVM: ok {arquivo}: {antigo.strip().splitlines()[0][:70]}")


# 1. Desenvolvido por GVM Sistemas
trocar("flutter/lib/common.dart",
       "        launchUrl(Uri.parse('https://rustdesk.com'));\n",
       f"        launchUrl(Uri.parse('{SITE}'));\n")

# 2. tela Instalar
trocar("flutter/lib/desktop/pages/install_page.dart",
       "'https://rustdesk.com/privacy.html'", f"'{SITE}'", vezes=2)

# 3. MSI: Contact, HelpLink e ReadMe
trocar("res/msi/preprocess.py", '"v": "https://github.com/rustdesk/rustdesk/issues/",', f'"v": "{SITE}",')
trocar("res/msi/preprocess.py", '"v": "https://github.com/rustdesk/rustdesk",', f'"v": "{SITE}",', vezes=2)

# 4a. tira a nota da parte colorida do card
trocar("flutter/lib/common/widgets/peer_card.dart", """                              if (_showNote(peer))
                                Row(
                                  children: [
                                    Expanded(
                                        child: Tooltip(
                                      message: peer.note,
                                      waitDuration: const Duration(seconds: 1),
                                      child: Text(
                                        peer.note,
                                        style: const TextStyle(
                                            color: Colors.white38,
                                            fontSize: 10),
                                        textAlign: TextAlign.center,
                                        overflow: TextOverflow.ellipsis,
                                      ),
                                    ))
                                  ],
                                ),
                            ],
                          ).paddingOnly(top: 4.0, left: 4.0, right: 4.0),""", """                            ],
                          ).paddingOnly(top: 4.0, left: 4.0, right: 4.0),""")

# 4b. nota embaixo do nome, na faixa de baixo do card
trocar("flutter/lib/common/widgets/peer_card.dart", """                      Expanded(
                          child: Row(children: [
                        getOnline(8, peer.online),
                        Expanded(
                            child: Text(
                          peer.alias.isEmpty ? formatID(peer.id) : peer.alias,
                          overflow: TextOverflow.ellipsis,
                          style: Theme.of(context).textTheme.titleSmall,
                        )),
                      ]).paddingSymmetric(vertical: 8)),
                      checkBoxOrActionMoreLandscape(peer, isTile: false),""", """                      Expanded(
                          child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              mainAxisSize: MainAxisSize.min,
                              children: [
                            Row(children: [
                              getOnline(8, peer.online),
                              Expanded(
                                  child: Text(
                                peer.alias.isEmpty ? formatID(peer.id) : peer.alias,
                                overflow: TextOverflow.ellipsis,
                                style: Theme.of(context).textTheme.titleSmall,
                              )),
                            ]),
                            if (_showNote(peer))
                              Tooltip(
                                message: peer.note,
                                waitDuration: const Duration(milliseconds: 500),
                                child: Text(
                                  peer.note,
                                  maxLines: 2,
                                  overflow: TextOverflow.ellipsis,
                                  style: TextStyle(
                                      fontSize: 12,
                                      height: 1.25,
                                      color: Theme.of(context)
                                          .textTheme
                                          .bodySmall
                                          ?.color),
                                ),
                              ).marginOnly(left: 14, top: 2),
                          ]).paddingSymmetric(vertical: 8)),
                      checkBoxOrActionMoreLandscape(peer, isTile: false),""")

# 4c. card do Catálogo com nota fica mais alto (2 linhas a mais)
trocar("flutter/lib/common/widgets/peers_view.dart", """                          ? SizedBox(
                              width: 220, height: 140, child: visibilityChild)""", """                          ? SizedBox(
                              width: 220,
                              height: widget.peerTabIndex == PeerTabIndex.ab &&
                                      peer.note.isNotEmpty
                                  ? 172
                                  : 140,
                              child: visibilityChild)""")

# 5. Editar anotação: janela grande
trocar("flutter/lib/common/widgets/dialog.dart", """    return CustomAlertDialog(
      title: Text(translate("Edit note")),
      content: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          TextField(
            controller: controller,
            autofocus: true,
            maxLines: 3,
            minLines: 1,
            maxLength: 300,
            decoration: InputDecoration(
              labelText: translate('Note'),
            ),
          ).workaroundFreezeLinuxMint(),""", """    // GVM: Enter pula linha (salvar é no OK); Esc fecha
    final focusNode = FocusNode(onKey: (FocusNode node, RawKeyEvent evt) {
      if (evt.logicalKey.keyLabel == 'Enter') {
        if (evt is RawKeyDownEvent) {
          final sel = controller.selection;
          final pos = sel.isValid ? sel.start : controller.text.length;
          final fim = sel.isValid ? sel.end : pos;
          controller.text =
              '${controller.text.substring(0, pos)}\\n${controller.text.substring(fim)}';
          controller.selection =
              TextSelection.fromPosition(TextPosition(offset: pos + 1));
        }
        return KeyEventResult.handled;
      }
      if (evt.logicalKey.keyLabel == 'Esc') {
        if (evt is RawKeyDownEvent) close();
        return KeyEventResult.handled;
      }
      return KeyEventResult.ignored;
    });
    final largura = (MediaQuery.of(context).size.width - 120).clamp(300.0, 900.0).toDouble();
    return CustomAlertDialog(
      title: Text(translate("Edit note")),
      contentBoxConstraints: BoxConstraints(maxWidth: largura),
      content: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: largura,
            child: TextField(
              controller: controller,
              focusNode: focusNode,
              autofocus: true,
              keyboardType: TextInputType.multiline,
              textInputAction: TextInputAction.newline,
              minLines: 12,
              maxLines: 12,
              maxLength: 2000,
              decoration: InputDecoration(
                labelText: translate('Note'),
                alignLabelWithHint: true,
                border: const OutlineInputBorder(),
              ),
            ).workaroundFreezeLinuxMint(),
          ),""")

print("GVM: patch do cliente aplicado")
