<p align="center">UFG - CAMPUS APARECIDA DE GOIÂNIA</p>

# 🛠️ Scripts de Gerenciamento - FCT/UFG

Repositório oficial de scripts PowerShell para administração de sistemas e laboratórios da Faculdade de Ciências e Tecnologia (FCT/UFG).  

🔧 **Ferramentas atualizadas** | 🚀 **Prontas para produção** | 📜 **Documentação clara**

---

## 📂 Scripts Disponíveis

| Nome do Script         | Descrição                                                                                  | Versão |
|------------------------|------------------------------------------------------------------------------------------|--------|
| [**`avisoLabs.ps1`**](avisoLabs.ps1) | Exibe avisos institucionais e regras de uso em laboratórios (canto superior direito da tela). | `v5`   |
| [**`fct.ps1`**](fct.ps1)               | Script modular para manutenção de sistemas Windows (GPOs, limpeza, redes, etc.).           | `v2.7` |
| *Em breve...*          | Novos scripts serão adicionados aqui!                                                    |        |

---

## 🚀 Funcionalidades Destacadas

### 🔖 `avisoLabs.ps1`
- Exibe informações em tempo real:
  - Nome do computador e IP local.
  - Regras de uso do laboratório.
  - Procedimentos ao sair.
  - Contato de suporte técnico.
- Interface visual customizada (transparente e responsiva).

### ⚙️ `fct.ps1`
- Menu interativo com 9 opções de administração:
  1. Listar programas instalados.
  2. Alterar nome do computador.
  3. Aplicar políticas de grupo (GPOs) da FCT.
  4. Restaurar GPOs padrão do Windows.
  5. Atualizar políticas de grupo.
  6. Resetar Microsoft Store.
  7. Limpeza avançada do sistema (arquivos temporários, contas, temas, etc.).
  8. Reiniciar computador.
  9. Sair do script.
- Suporte a execução com privilégios elevados.

---

## 📥 Como Usar

### Pré-requisitos
- PowerShell 5.0 ou superior.
- Permissões de administrador (para `fct.ps1`).


### Execução

1. **Baixar o Script**: O script pode ser baixado diretamente do repositório GitHub.
2. **Executar o Script**: Execute o script com o seguinte comando no PowerShell:

   ```powershell
   irm https://raw.githubusercontent.com/ti-fct/scripts/refs/heads/main/fct.ps1 | iex
   ```

   ```powershell
   Set-SmbClientConfiguration -EnableInsecureGuestLogons $true
   ```

---

## 🛠️ Futuras Atualizações

- **Novos scripts planejados**:
- Backup automatizado de estações.
- Monitoramento de hardware em tempo real.
- Melhorias na documentação e exemplos de uso.

---

## 🤝 Contribuição

Contribuições são bem-vindas! Siga estas etapas:

1. Faça um fork do projeto.
2. Crie uma branch: `git checkout -b minha-feature`.
3. Commit suas mudanças: `git commit -m 'Adicionei um script incrível'`.
4. Push para a branch: `git push origin minha-feature`.
5. Abra um **Pull Request**.

---

## 📜 Licença

Distribuído sob a licença MIT. Veja [LICENSE](LICENSE) para mais detalhes.

---

## 👨💻 Autores

- **Departamento de TI - FCT/UFG**
<p align="center">
<img src="https://img.shields.io/badge/Powered%20by-PowerShell-blue?style=for-the-badge&logo=powershell" alt="Powered by PowerShell">
</p>

```

### Personalize

- Substitua `https://github.com/seu-usuario/seu-repositorio.git` pelo link real do seu repositório.
- Adicione ou ajuste seções conforme novos scripts forem incluídos.
- Atualize o e-mail de suporte (`ti@fct.ufg.br`) se necessário.
