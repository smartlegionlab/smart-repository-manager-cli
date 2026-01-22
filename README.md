# Smart Repository Manager CLI <sup>v0.1.2</sup>

A comprehensive command-line tool for managing GitHub repositories with advanced synchronization, SSH configuration management, and intelligent local repository management.

---

[![GitHub release (latest by date)](https://img.shields.io/github/v/release/smartlegionlab/smart-repository-manager-cli)](https://github.com/smartlegionlab/smart-repository-manager-cli/)
![GitHub top language](https://img.shields.io/github/languages/top/smartlegionlab/smart-repository-manager-cli)
[![GitHub](https://img.shields.io/github/license/smartlegionlab/smart-repository-manager-cli)](https://github.com/smartlegionlab/smart-repository-manager-cli/blob/master/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/smartlegionlab/smart-repository-manager-cli?style=social)](https://github.com/smartlegionlab/smart-repository-manager-cli/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/smartlegionlab/smart-repository-manager-cli?style=social)](https://github.com/smartlegionlab/smart-repository-manager-cli/network/members)

---
## 🚀 Overview

Smart Repository Manager CLI is a powerful tool that helps you:
- Manage GitHub repositories locally with intelligent synchronization
- Configure and validate SSH for secure Git operations
- Monitor repository health and status
- Perform batch operations on multiple repositories
- Maintain organized local storage structure

---

## 📦 Core Features

### 1. **System Check & Configuration**
- **Full System Checkup**: Comprehensive 8-step verification process
- **Directory Structure Management**: Automatic creation of organized user directories
- **Configuration Management**: Persistent user and token storage
- **Network Validation**: Internet connectivity and DNS resolution checks

### 2. **GitHub Integration**
- **Token Management**: Secure storage and validation of GitHub Personal Access Tokens
- **User Authentication**: Multi-user support with active user switching
- **Repository Discovery**: Fetch all user repositories (public, private, forked, archived)
- **API Rate Limit Monitoring**: Real-time GitHub API usage tracking

### 3. **SSH Configuration & Management**
- **SSH Validation**: Comprehensive SSH setup verification
- **Key Generation**: Support for multiple key types (ED25519, RSA, ECDSA, DSA)
- **Configuration Management**: Automatic SSH config creation and validation
- **Connection Testing**: Verify SSH connectivity to GitHub
- **Permission Fixing**: Automatic repair of SSH file permissions

### 4. **Repository Management**
- **Repository Listing**: View all repositories with filtering options
- **Search Functionality**: Find repositories by name
- **Language Statistics**: Analyze repository language distribution
- **Health Checking**: Verify local repository integrity
- **Storage Management**: Monitor and manage local repository storage

### 5. **Intelligent Synchronization**
- **Smart Sync**: Automatic detection of needed operations (clone/update/repair)
- **Batch Operations**: Process multiple repositories simultaneously
- **Update Detection**: Identify repositories needing updates
- **Auto-Repair**: Automatic fixing of broken repositories
- **Progress Tracking**: Real-time sync progress and statistics

### 6. **Local Storage Management**
- **Organized Structure**: Automatic directory organization by user
- **Size Monitoring**: Track storage usage
- **Cleanup Tools**: Remove individual or all local repositories
- **Temporary File Management**: Automatic cleanup of temporary files

---

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Git installed and configured
- GitHub Personal Access Token (with repo scope)

### Setup
```bash
# Clone the repository
git clone https://github.com/smartlegionlab/smart_repository_manager_cli.git

# Install dependencies
pip install -r requirements.txt

# Run the CLI
python app.py
```

---

## 📋 Usage Guide

### First Run
1. **Initial Checkup**: The tool automatically runs a full system check
2. **Token Setup**: Enter your GitHub Personal Access Token when prompted
3. **SSH Configuration**: Follow prompts to set up SSH if not configured

### Main Menu Options

#### 1. **User Information**
- View GitHub profile details
- See repository statistics
- Check account creation date

#### 2. **Token Information**
- View token scopes and limits
- Monitor API rate limits
- Check token creation date

#### 3. **Repository Management**
- List all repositories with status indicators
- Search for specific repositories
- View language statistics
- Check individual repository status
- Run repository health checks

#### 4. **Synchronization**
- **Sync All**: Clone missing and update existing repositories
- **Update Needed Only**: Only update repositories with new commits
- **Clone Missing Only**: Only clone repositories not present locally
- **Sync with Repair**: Fix broken repositories while syncing

#### 5. **SSH Configuration**
- Check SSH setup status
- Generate new SSH keys
- View existing SSH keys
- Fix SSH permissions
- Add GitHub to known_hosts
- Create SSH configuration
- Test SSH connection
- View detailed SSH information

#### 6. **Storage Management**
- View storage usage statistics
- Delete individual repositories
- Clear all local repositories
- Check storage information

#### 7. **System Information**
- View application configuration
- Check system status
- Review repository statistics
- Monitor SSH status

#### 8. **Run Checkup**
- Perform complete system verification
- Identify and fix issues
- Generate detailed logs

#### 9. **Clean Temporary Files**
- Remove temporary files
- Free up disk space

---

## 🔧 Configuration

### Directory Structure
```
~/smart_repo_manager/
├── config.json              # Application configuration
├── username/                # User-specific directories
│   ├── repositories/       # Local repository clones
│   ├── archives/          # Backup archives
│   ├── logs/             # Operation logs
│   ├── backups/          # Manual backups
│   └── temp/             # Temporary files (auto-cleaned)
└── checkup_results_*.json  # Checkup result logs
```

### Environment Setup
1. **GitHub Token**: Create a token with `repo` scope at https://github.com/settings/tokens
2. **SSH Keys**: Generate SSH keys if not already present
3. **Git Configuration**: Ensure `user.name` and `user.email` are set globally

---

## ⚙️ Technical Details

### Core Components
- **Models**: Data structures for users, repositories, tokens, and SSH configurations
- **Services**: Business logic for GitHub, Git, SSH, network, and sync operations
- **CLI Interface**: User-friendly command-line interface with menus and prompts
- **Validation**: Comprehensive input validation and error handling

### Error Handling
- Automatic retry mechanisms for failed operations
- Detailed error logging and reporting
- Graceful degradation when features are unavailable
- User-friendly error messages

### Performance Features
- Concurrent operations where possible
- Caching of repository data
- Progress tracking for long operations
- Efficient memory usage

---

## 🎯 Use Case

### For Developers
- Keep local copies of all GitHub repositories synchronized
- Quickly clone multiple repositories for new machine setup
- Monitor repository health and fix issues automatically
- Manage SSH configurations across multiple machines

---

## 📊 Monitoring & Logging

### Checkup Results
Detailed JSON logs are saved for each system checkup, including:
- Timestamp and duration
- Success/failure status of each step
- Configuration details
- Error messages and recommendations

### Real-time Status
- Progress indicators for long operations
- Immediate feedback for user actions
- Status summaries after operations complete

---

## 🔒 Security Features

- **Token Security**: GitHub tokens stored locally with appropriate permissions
- **SSH Security**: Proper file permissions enforced for SSH keys
- **Input Validation**: All user input validated before processing
- **Error Handling**: Sensitive information not exposed in error messages

---

## 🚨 Troubleshooting

### Common Issues

1. **SSH Connection Failed**
   - Run SSH check from the SSH menu
   - Generate new SSH key if needed
   - Add SSH key to GitHub account

2. **Token Authentication Failed**
   - Verify token has correct scopes (repo)
   - Generate new token if expired
   - Check network connectivity to GitHub

3. **Repository Sync Fails**
   - Check SSH configuration
   - Verify repository permissions
   - Ensure sufficient disk space

4. **Network Issues**
   - Run network check from system checkup
   - Verify DNS resolution
   - Check firewall settings

### Getting Help
- Review checkup result logs in `~/smart_repo_manager/<username>/logs/`
- Check error messages in the CLI interface
- Verify GitHub token permissions
- Ensure SSH keys are added to GitHub

---

## 📈 Performance Tips

- Run regular checkups to identify issues early
- Use "Update Needed Only" for frequent syncs
- Clean temporary files periodically
- Monitor storage usage to prevent disk space issues
- Generate SSH keys with appropriate types (ED25519 recommended)

---

## 🔄 Updates & Maintenance

### Regular Maintenance Tasks
1. **Run System Checkup**: Weekly to ensure everything works
2. **Clean Temporary Files**: Monthly or as needed
3. **Review Storage Usage**: Periodically to manage disk space
4. **Update GitHub Token**: Annually or when permissions change

### Data Backup
- Configuration files: `~/smart_repo_manager/config.json`
- User data: `~/smart_repo_manager/<username>/`
- Log files: `~/smart_repo_manager/<username>/logs/`

---

## 🙏 Acknowledgments

- GitHub API for repository access
- Python community for excellent libraries
- Contributors and testers: [@aixandrolab](https://github.com/aixandrolab)

---

## 📄 License

BSD 3-Clause License - See [LICENSE](LICENSE) file for details.

Copyright © 2025, Alexander Suvorov. All rights reserved.

---

## Related Projects

This core library powers two complete implementations:

### [Core Version](https://github.com/smartlegionlab/smart-repository-manager-core) 
A Python library for managing Git repositories with intelligent synchronization, SSH configuration validation, and GitHub integration.

### [GUI Version](https://github.com/smartlegionlab/smart-repository-manager-gui)  
A desktop graphical user interface that offers visual management of repositories, SSH configuration, and synchronization tasks. Built for users who prefer point-and-click interaction.

Both implementations use this core library as their engine, ensuring consistent behavior and feature parity across interfaces.

---

## Disclaimer

**Important**: This software is provided "as-is" without any warranties or guarantees. The developers are not responsible for:

- Data loss or corruption
- Repository damage or unintended modifications
- Security breaches or token exposure
- Network issues or connectivity problems
- Any other direct or indirect damages

**Use at your own risk**. Always maintain backups of your repositories and tokens. This project is in active development and may contain bugs or incomplete features.

## Development Status

⚠️ **Active Development** - This project is under active development. Features may change, and stability is not guaranteed. Not recommended for production use without thorough testing.

## Support

For issues and questions, please check the GitHub repository:  
[https://github.com/smartlegionlab/smart-repository-manager-cli](https://github.com/smartlegionlab/smart-repository-manager-cli)

---

**Developer**: [Alexander Suvorov]( https://github.com/smartlegionlab/)
**Contact**: [smartlegiondev@gmail.com](mailto:smartlegiondev@gmail.com)

---

## Screenshot

![Smart Repository Manager Cli Logo](https://github.com/smartlegionlab/smart-repository-manager-cli/blob/master/data/images/smart_repository_manager_cli.png)

