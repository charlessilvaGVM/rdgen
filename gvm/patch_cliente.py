"""GVM Suporte - ajustes no código do cliente (RustDesk 1.4.9) antes de compilar o Windows (20/10/2026).

Uso no workflow: python gvm/patch_cliente.py <pasta do rustdesk>
Cada troca precisa casar exatamente uma vez; se o código do RustDesk mudar, o build falha aqui.
  1. "Desenvolvido por GVM Sistemas" (loadPowered) abre gvmsistemas.com.br, e não rustdesk.com
  2. tela Instalar: link do contrato de licença -> gvmsistemas.com.br
  3. Aplicativos instalados do Windows (MSI): links de ajuda/contato -> gvmsistemas.com.br
  4. Catálogo: a observação (nota) sai da parte colorida do card e NÃO aparece no card (costuma ter senha;
     29/10/2026): só ao parar o mouse sobre o nome e no "Editar anotação"
  5. "Editar anotação": janela de 900 px, caixa de 12 linhas com rolagem, Enter = nova linha, até 2000 caracteres
  6. Início automático (22/10/2026): o serviço já é "automático"; agora o Windows também o RELIGA se cair
     (sc failure: 5 s / 10 s / 60 s), tanto no instalar do .exe quanto no .msi
  7. .msi: o atalho "GVM_Suporte Tray" na Inicialização (abre o app na bandeja em todo login) é sempre criado
  8. "Parar serviço" escondido (Configurações e bandeja): no Windows ele APAGA o serviço e o atalho da
     Inicialização, e o PC some até alguém reinstalar. Se o serviço estiver parado, o botão "Iniciar" continua
  9/10. .msi: fecha tudo antes de atualizar; coletor de inventário com tarefa agendada
  11. mensagem nova no chat: pisca o ícone na barra de tarefas e toca o som do Windows (29/10/2026)
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

# 4b. (29/10/2026, pedido do usuário) a nota NÃO aparece no card (costuma ter senha): só ao parar o
#     mouse sobre o nome (Catálogo) e no "Editar anotação". Antes (20/10) ela ficava embaixo do nome.
trocar("flutter/lib/common/widgets/peer_card.dart", """                        Expanded(
                            child: Text(
                          peer.alias.isEmpty ? formatID(peer.id) : peer.alias,
                          overflow: TextOverflow.ellipsis,
                          style: Theme.of(context).textTheme.titleSmall,
                        )),
                      ]).paddingSymmetric(vertical: 8)),
                      checkBoxOrActionMoreLandscape(peer, isTile: false),""", """                        Expanded(
                            child: _showNote(peer)
                                ? Tooltip(
                                    message: peer.note,
                                    waitDuration:
                                        const Duration(milliseconds: 500),
                                    child: Text(
                                      peer.alias.isEmpty
                                          ? formatID(peer.id)
                                          : peer.alias,
                                      overflow: TextOverflow.ellipsis,
                                      style: Theme.of(context)
                                          .textTheme
                                          .titleSmall,
                                    ))
                                : Text(
                                    peer.alias.isEmpty
                                        ? formatID(peer.id)
                                        : peer.alias,
                                    overflow: TextOverflow.ellipsis,
                                    style:
                                        Theme.of(context).textTheme.titleSmall,
                                  )),
                      ]).paddingSymmetric(vertical: 8)),
                      checkBoxOrActionMoreLandscape(peer, isTile: false),""")

# 4c. (29/10/2026) visão em lista/blocos: idem, a nota sai da linha do card e vai para o tooltip do nome
trocar("flutter/lib/common/widgets/peer_card.dart", "    final showNote = _showNote(peer);\n",
       "    final showNote = false; // GVM: a nota (pode ter senha) só aparece no tooltip\n")
trocar("flutter/lib/common/widgets/peer_card.dart", """                              message: name,
                              waitDuration: const Duration(seconds: 1),
                              child: Align(""", """                              message: _showNote(peer)
                                  ? '$name\\n${peer.note}'
                                  : name,
                              waitDuration: const Duration(seconds: 1),
                              child: Align(""")

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

# 6. serviço com recuperação automática (instalar pelo .exe)
trocar("src/platform/windows.rs",
       'sc create {app_name} binpath= \\"\\\\\\"{exe}\\\\\\" --service\\" start= auto DisplayName= \\"{app_name} Service\\"\nsc start {app_name}\n',
       'sc create {app_name} binpath= \\"\\\\\\"{exe}\\\\\\" --service\\" start= auto DisplayName= \\"{app_name} Service\\"\nsc start {app_name}\n'
       'sc failure {app_name} reset= 86400 actions= restart/5000/restart/10000/restart/60000\n')

# 6. serviço com recuperação automática (.msi): roda o sc.exe logo depois do CreateStartService
trocar("res/msi/Package/Components/RustDesk.wxs",
       '\t\t<CustomAction Id="TryStopDeleteService.SetParam"',
       '\t\t<CustomAction Id="GvmServiceRecovery" Directory="INSTALLFOLDER_INNER" ExeCommand="&quot;[System64Folder]sc.exe&quot; failure $(var.Product) reset= 86400 actions= restart/5000/restart/10000/restart/60000" Execute="deferred" Impersonate="no" Return="ignore" />\n'
       '\t\t<CustomAction Id="TryStopDeleteService.SetParam"')
trocar("res/msi/Package/Components/RustDesk.wxs",
       '\t\t\t<Custom Action="CustomActionHello" Before="InstallFinalize" />',
       '\t\t\t<Custom Action="GvmServiceRecovery" After="CreateStartService" Condition="(NOT (Installed AND REMOVE AND NOT UPGRADINGPRODUCTCODE)) AND (NOT STOP_SERVICE=&quot;&apos;Y&apos;&quot;) AND (NOT CC_CONNECTION_TYPE=&quot;outgoing&quot;)" />\n\n'
       '\t\t\t<Custom Action="CustomActionHello" Before="InstallFinalize" />')

# 7. .msi: atalho da bandeja na Inicialização sempre (sem depender da caixinha do instalador)
trocar("res/msi/Package/Components/RustDesk.wxs",
       'Condition="STARTUPSHORTCUTS = 1 AND (NOT CC_CONNECTION_TYPE=&quot;outgoing&quot;)"',
       'Condition="NOT CC_CONNECTION_TYPE=&quot;outgoing&quot;"')

# 8. esconder "Parar serviço" (equivale ao hide-stop-service=Y da configuração)
trocar("flutter/lib/desktop/pages/desktop_setting_page.dart",
       "    final hideStopService =\n        bind.mainGetBuildinOption(key: kOptionHideStopService) == 'Y';\n",
       "    const hideStopService = true; // GVM: parar o serviço apaga o serviço no Windows\n")
trocar("src/tray.rs",
       '    let hide_stop_service = crate::ui_interface::get_builtin_option(\n        hbb_common::config::keys::OPTION_HIDE_STOP_SERVICE,\n    ) == "Y";\n',
       '    let hide_stop_service = true; // GVM: parar o serviço apaga o serviço no Windows\n')

# 9. .msi: ao atualizar, para o serviço e fecha todos os GVM_Suporte.exe antes de trocar os arquivos
#    (sem a janela "feche os aplicativos"). 1ª tentativa antes do InstallValidate (pode não ter
#    permissão), 2ª como SYSTEM logo depois do InstallInitialize
#    (deferred precisa ficar entre InstallInitialize e InstallFinalize). O serviço volta no CreateStartService
#    e a bandeja no LaunchAppTray (LAUNCH_TRAY_APP=Y é o padrão).
GVM_PARAR = ('ExeCommand="&quot;[System64Folder]cmd.exe&quot; /c sc stop $(var.Product) &amp; '
             'taskkill /F /T /IM $(var.Product).exe" Return="ignore"')
trocar("res/msi/Package/Components/RustDesk.wxs",
       '\t\t<CustomAction Id="TryStopDeleteService.SetParam"',
       f'\t\t<CustomAction Id="GvmPararTudoAntes" Directory="INSTALLFOLDER_INNER" {GVM_PARAR} Execute="immediate" />\n'
       f'\t\t<CustomAction Id="GvmPararTudo" Directory="INSTALLFOLDER_INNER" {GVM_PARAR} Execute="deferred" Impersonate="no" />\n'
       '\t\t<CustomAction Id="TryStopDeleteService.SetParam"')
trocar("res/msi/Package/Components/RustDesk.wxs",
       '\t\t\t<Custom Action="CustomActionHello" Before="InstallFinalize" />',
       '\t\t\t<Custom Action="GvmPararTudoAntes" Before="InstallValidate" Condition="WIX_UPGRADE_DETECTED" />\n'
       '\t\t\t<Custom Action="GvmPararTudo" After="InstallInitialize" Condition="WIX_UPGRADE_DETECTED" />\n\n'
       '\t\t\t<Custom Action="CustomActionHello" Before="InstallFinalize" />')

# 10. .msi: coletor de inventário (gvm-inventario.ps1, posto na pasta do app pelo workflow) cria a tarefa agendada
#     "GVM Suporte - Inventario" (SYSTEM) ao instalar/atualizar; ao desinstalar de vez, apaga a tarefa.
trocar("res/msi/Package/Components/RustDesk.wxs",
       '\t\t<CustomAction Id="TryStopDeleteService.SetParam"',
       '\t\t<CustomAction Id="GvmInventarioInstalar" Directory="INSTALLFOLDER_INNER" ExeCommand="&quot;[System64Folder]WindowsPowerShell\\v1.0\\powershell.exe&quot; -NoProfile -NonInteractive -ExecutionPolicy Bypass -File &quot;[INSTALLFOLDER_INNER]gvm-inventario.ps1&quot; -Instalar" Execute="deferred" Impersonate="no" Return="ignore" />\n'
       '\t\t<CustomAction Id="GvmInventarioRemover" Directory="INSTALLFOLDER_INNER" ExeCommand="&quot;[System64Folder]schtasks.exe&quot; /Delete /TN &quot;GVM Suporte - Inventario&quot; /F" Execute="deferred" Impersonate="no" Return="ignore" />\n'
       '\t\t<CustomAction Id="TryStopDeleteService.SetParam"')
trocar("res/msi/Package/Components/RustDesk.wxs",
       '\t\t\t<Custom Action="CustomActionHello" Before="InstallFinalize" />',
       '\t\t\t<Custom Action="GvmInventarioInstalar" Before="InstallFinalize" Condition="NOT (REMOVE=&quot;ALL&quot;) AND (NOT CC_CONNECTION_TYPE=&quot;outgoing&quot;)" />\n'
       '\t\t\t<Custom Action="GvmInventarioRemover" Before="RemoveFiles" Condition="REMOVE=&quot;ALL&quot; AND NOT UPGRADINGPRODUCTCODE" />\n\n'
       '\t\t\t<Custom Action="CustomActionHello" Before="InstallFinalize" />')

# 11. (29/10/2026) mensagem nova no chat: se o GVM Suporte não estiver na frente, o ícone dele PISCA na barra
#     de tarefas (até a pessoa clicar, como no AnyDesk) e toca o som de aviso do Windows. Vale para os dois
#     lados: técnico (janela da conexão) e cliente (janela do chat/permissões). Arquivo novo gvm_aviso.dart.
GVM_AVISO = """// GVM Suporte: aviso de mensagem nova no chat (pisca o ícone na barra de tarefas e toca o som do Windows).
import 'dart:ffi';
import 'dart:io';

import 'package:ffi/ffi.dart';
import 'package:flutter/foundation.dart';

final class _FlashInfo extends Struct {
  @Uint32()
  external int cbSize;
  @IntPtr()
  external int hwnd;
  @Uint32()
  external int dwFlags;
  @Uint32()
  external int uCount;
  @Uint32()
  external int dwTimeout;
}

void gvmAvisarMensagem() {
  if (!Platform.isWindows) return;
  try {
    final user32 = DynamicLibrary.open('user32.dll');
    final kernel32 = DynamicLibrary.open('kernel32.dll');
    final findWindowEx = user32.lookupFunction<
        IntPtr Function(IntPtr, IntPtr, Pointer<Utf16>, Pointer<Utf16>),
        int Function(int, int, Pointer<Utf16>, Pointer<Utf16>)>('FindWindowExW');
    final getWindowPid = user32.lookupFunction<
        Uint32 Function(IntPtr, Pointer<Uint32>),
        int Function(int, Pointer<Uint32>)>('GetWindowThreadProcessId');
    final isVisible = user32
        .lookupFunction<Int32 Function(IntPtr), int Function(int)>('IsWindowVisible');
    final getForeground = user32
        .lookupFunction<IntPtr Function(), int Function()>('GetForegroundWindow');
    final flashWindowEx = user32.lookupFunction<
        Int32 Function(Pointer<_FlashInfo>),
        int Function(Pointer<_FlashInfo>)>('FlashWindowEx');
    final messageBeep = user32
        .lookupFunction<Int32 Function(Uint32), int Function(int)>('MessageBeep');
    final meuPid = kernel32
        .lookupFunction<Uint32 Function(), int Function()>('GetCurrentProcessId')();

    messageBeep(0x40); // MB_ICONASTERISK
    final pid = calloc<Uint32>();
    final info = calloc<_FlashInfo>();
    try {
      final frente = getForeground();
      if (frente != 0) {
        getWindowPid(frente, pid);
        if (pid.value == meuPid) return; // a pessoa já está olhando o GVM Suporte
      }
      var h = 0;
      for (var i = 0; i < 10000; i++) {
        h = findWindowEx(0, h, nullptr, nullptr);
        if (h == 0) break;
        pid.value = 0;
        getWindowPid(h, pid);
        if (pid.value != meuPid || isVisible(h) == 0) continue;
        info.ref
          ..cbSize = sizeOf<_FlashInfo>()
          ..hwnd = h
          ..dwFlags = 0x0F // FLASHW_ALL | FLASHW_TIMERNOFG: pisca até a janela vir para a frente
          ..uCount = 0
          ..dwTimeout = 0;
        flashWindowEx(info);
      }
    } finally {
      calloc.free(pid);
      calloc.free(info);
    }
  } catch (e) {
    debugPrint('GVM: aviso de mensagem falhou: $e');
  }
}
"""
with open(os.path.join(RAIZ, "flutter/lib/gvm_aviso.dart"), "w", encoding="utf-8", newline="\n") as f:
    f.write(GVM_AVISO)
print("GVM: ok flutter/lib/gvm_aviso.dart (novo)")
trocar("flutter/lib/models/chat_model.dart", "import '../main.dart';\n",
       "import '../main.dart';\nimport '../gvm_aviso.dart';\n")
trocar("flutter/lib/models/chat_model.dart", "    latestReceivedKey = messagekey;\n",
       "    if (isDesktop) gvmAvisarMensagem(); // GVM: pisca na barra de tarefas e toca o som\n"
       "    latestReceivedKey = messagekey;\n")

print("GVM: patch do cliente aplicado")
