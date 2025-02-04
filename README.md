<p align="center">UFG - CAMPUS APARECIDA DE GOIÂNIA</p>

# 🛠️ Scripts de Gerenciamento - FCT/UFG

Repositório oficial de scripts PowerShell para administração de sistemas e laboratórios da Faculdade de Ciências e Tecnologia (FCT/UFG).  

---

## 📂 Scripts Disponíveis

| Nome do Script         | Descrição                                                                                  | Versão |
|------------------------|------------------------------------------------------------------------------------------|--------|
| [**`avisoLabs.ps1`**](avisoLabs.ps1) | Exibe avisos institucionais e regras de uso em laboratórios (canto superior direito da tela). | `v5`   |
| [**`fixLabs.ps1`**](fixLabs.ps1)               | Script modular para manutenção de labs com Windows para quem não tem AD (GPOs, limpeza, redes, etc.).           | `v3` |
| *Em breve...*          | Novos scripts serão adicionados aqui!                                                    |        |

---

## 🚀 Funcionalidades Destacadas

### 🔖 `avisoLabs.ps1`
- Exibe seguinte aviso no desktop dos labs:
  - Nome do computador.
  - Regras de uso do laboratório.
  - Procedimentos ao sair.
  - Contato de suporte técnico.
- Interface visual customizada (transparente e responsiva).

### ⚙️ `fixLabs.ps1`
- Menu interativo com diversas opções de administração:
 1. 📜 Listar Programas Instalados
 2. 💻 Alterar Nome do Computador
 3. 🏛 Aplicar GPOs da FCT
 4. 🧹 Restaurar GPOs Padrão do Windows
 5. 🔄 Atualizar GPOs
 6. 🛒 Reset Windows Store
 7. 🔓 Habilitar Acesso SMB
 8. 🧼 Limpeza Geral do Windows
 9. 🚨 Adiciona Aviso no Desktop
- Suporte a execução com privilégios elevados.

---

## 📥 Como Usar

### Pré-requisitos
- PowerShell 5.0 ou superior.
- Python 3 ou superior.
- Permissões de administrador.


### Execução

1. **Executar o Script**: Execute o script com o seguinte comando no PowerShell:

   ```powershell
   irm https://raw.githubusercontent.com/ti-fct/scripts/refs/heads/main/fct.ps1 | iex
   ```

---

## 🛠️ Futuras Atualizações

- **Novos scripts planejados**:
- Backup automatizado de estações.
- Melhoria na extração de GPOs.
- Melhorias na documentação e exemplos de uso.
- Lista de softwares usados nos laboratórios.

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
<img src="https://img.shields.io/badge/Powered%20by-PowerShell-blue?style=for-the-badge&logo=powershell" alt="Powered by PowerShell"> <img src="https://img.shields.io/badge/Powered%20by-Python-3776AB?style=for-the-badge&logo=python" alt="Powered by Python">
</p>
