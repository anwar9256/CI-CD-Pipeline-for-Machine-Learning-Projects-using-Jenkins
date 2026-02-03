# CI/CD Pipeline for a Continuously Learning ML Project

## Objective

Create an SBERT and FAISS based search bar and ensure that any change in the training data, i.e feature store, or any change in the code, i.e resulting from hyper-parameter tuning or bert/faiss model upgrade, will trigger an end-to-end training job without disruption of the service already in production

# Pre-requisites

- Setup EC2 Instance
- Setup docker and docker-compose
- search engine bar up and ready

# Prepare Codebase Github Repositories

**Repos**

Note: Please update the GitHub URL and credentials with your own GitHub credentials. The repository that was used earlier to demonstrate the project cannot be used for the execution now.

- search bar repo: [https://github.com/Github-username/Github-Repo-Name.git](https://github.com/Github-username/Github-Repo-Name.git)
    - Production branch: `prod`
    - Staging branch: `stage`
- jenkins-server repo: [https://github.com/Github-username/Github-Repo-Name.git](https://github.com/Github-username/Github-Repo-Name.git)
    - branch-name: `jenkinsserver`

**Create personal access token**

- Ensure that you are logged in github
- Go to [https://github.com/settings/tokens](https://github.com/settings/tokens)
- Click on “Generate new token” and choose “classic”.
    
    
- Fill in some notes to describe your token
- Select the expiration length
- Check box on: *admin:org_hook, admin:public_key, admin:repo_hook, admin:ssh_signing_key, repo, user*
- Copy the token and save it in a safe place
    
    ```bash
    # personal access token - expire on 2022-12-17
    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 (Create your own Github Token)
    ```
    

# Deploy Search Bar App on EC2 Instance

**Note:**

- Instance type: t2.medium, ubuntu 22.04, 30GB
- Instance public IP: [http://EC2-Instance-IP/] - Go to the EC2 Instance and copy the Public IPv4 address of your EC2 Instance
- SSH in the instance
    
    ```bash
    ssh -i "<path-to-pemfile.pem>" ubuntu@<instance-url>
    ```
    
- Create a folder for logs
    
    ```bash
    mkdir logs
    ```
    
- Install apt packages: git, tree
    
    ```bash
    sudo apt-get update
    sudo apt-get install git tree
    ```
    
- Install conda
    
    ```bash
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
    && sudo mkdir /root/.conda \
    && bash Miniconda3-latest-Linux-x86_64.sh -b \
    && rm -f Miniconda3-latest-Linux-x86_64.sh
    export PATH="/home/ubuntu/miniconda3/bin:${PATH}"
    ```
    
- Clone search bar repo and pull `repo` branch for most recent updates
    
    ```bash
    git clone https://github.com/Github-username/Github-Repo-Name.git
    cd sbert-search-bar
    git remote set-url origin https://<Github-username>:<personal-access-token>@github.com/<Github-username>/<Github-Repo-Name>.git
    git fetch --all
    git pull origin prod
    ```
    
- Create conda environment and install all requirements
    
    ```bash
    conda create -y -n sbar-env python=3.10
    source activate sbar-env
    pip install -r requirements.txt
    ```
    
- Train search index and run the app in the background using `nohup`
    
    ```bash
    python3 engine.py
    nohup streamlit run app.py &>/dev/null &
    ```
    

# Set up Jenkins Server on EC2 Instance

**Note:**

- Instance type: t2.large, ubuntu 22.04, 30GB
- Instance public IP: [http://EC2-Instance-IP/] - Go to the EC2 Instance and copy the Public IPv4 address of your EC2 Instance
- SSH in the instance
    
    ```bash
    ssh -i "<path-to-pemfile.pem>" ubuntu@<instance-url>
    ```
    
- Install apt packages: git, tree
    
    ```bash
    sudo apt-get update
    sudo apt-get install git tree
    ```
    
- Install docker and docker-compose
    
    ```bash
    # Installing Docker-ce
    sudo apt update
    sudo apt install apt-transport-https ca-certificates curl software-properties-common
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt update
    apt-cache policy docker-ce
    sudo apt install docker-ce
    sudo systemctl enable --now docker
    
    # Adding docker-compose-plugin
    sudo apt install python3-pip
    pip install --upgrade pip
    sudo pip install docker-compose
    ```
    
- Clone jenkins-server repo
    
    ```bash
    git clone https://github.com/Github-username/Github-Repo-Name.git
    cd camille_projects
    git remote set-url origin https://<Github-username>:<personal-access-token>@github.com/<Github-username>/<Github-Repo-Name>.git
    git fetch jenkinsserver
    git pull origin jenkinsserver
    ```
    
- Instance Jenkins on a docker container
    
    ```bash
    cd jenkins
    sudo docker compose build
    sudo docker compose up -d
    ```
    
- Configure Jenkins server for first time
    - Copy one time log in pass
        
        ```bash
        sudo docker logs jenkins | less
        ```
        
    -  Instance public IP: [http://EC2-Instance-IP/] - Go to the EC2 Instance and copy the Public IPv4 address of your EC2 Instance and follow steps
- Install default plugins
- Install additional plugins
    - Github Pull Request Builder (Deprecated)
        You can use multibranch pipeline in Jenkins
    - publish-over-ssh
- Setup security tokens
    - Github personal access token

# Jenkins Jobs

- update search bar
- data monitor job
- code monitor job

### Job 1: Update search bar
    
- SSH into Searchbar server, update the code or data and restart the app
- Freestyle job
- Trigger by either  `code monitor job` or `data monitor job`
- Bash Script

```groovy
        cd /home/ubuntu/sbert-search-bar
        echo "------------BEGIN-------------">/home/ubuntu/logs/sbert-search-bar.txt
        echo "last job start: $(date)">>/home/ubuntu/logs/sbert-search-bar.txt
        export PATH="/home/ubuntu/miniconda3/bin:${PATH}"
        source activate sbar-env
        git checkout prod
        git stash
        git pull origin prod --rebase
        pip3 install -r requirements.txt
        python3 engine.py>>/home/ubuntu/logs/sbert-search-bar.txt
        kill -9 $(pgrep streamlit) || echo "Process Not Found!"
        nohup streamlit run app.py &>/dev/null &
        echo "last job end: $(date)">>/home/ubuntu/logs/sbert-search-bar.txt
        
        echo "[info] pushing new dataset back to github">>/home/ubuntu/logs/sbert-search-bar.txt
        git add data/project_mappings.csv
        git commit -m "[searchbar-server autocommit] training data updated @ timestamp $(date +%s)"
        git pull origin prod --rebase
        git push origin prod
        echo "------------END-------------">>/home/ubuntu/logs/sbert-search-bar.txt
```
        
- Demo how to setup update search bar job
- Create password to log into the search bar VM
     
```groovy
        sudo passwd ubuntu
        sudo sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
        sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config
        sudo sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config.d/60-cloudimg-settings.conf
        echo "PasswordAuthentication yes" | sudo tee -a /etc/ssh/sshd_config.d/60-cloudimg-settings.conf
        sudo systemctl daemon-reload
        sudo systemctl restart ssh
```
- Configure Publish Over SSH Jenkins plugin
- Create a freestyle project
- Test

### Job 2: Data monitor

- Runs periodically: Keeps checking whether the data currently in production is same as training data of the model currently in production

- Pipeline job

- Jenkinsfile

```groovy
pipeline {
    agent any
    environment {
        PATH = "$WORKSPACE/miniconda/bin:$PATH"
    }
    stages {
        stage('Repos') {
            steps {
                // clean workspace 
                cleanWs(
                    deleteDirs: true,
                    notFailBuild: true,
                    patterns: [[pattern: '*', type: 'INCLUDE']
                ])
                
                script {
                    // retrieve github personal access token from jenkins parameters
                    def ghPersonalAccessToken = params['GH_PERSONAL_ACCESS_TOKEN']
                    
                    // checkout repo in prod branch
                    checkout([
                        $class: 'GitSCM', 
                        branches: [[name: "origin/prod"]], 
                        doGenerateSubmoduleConfigurations: false, 
                        extensions: [], 
                        submoduleCfg: [], 
                        userRemoteConfigs: [[credentialsId: "github-credentials", url: "https://<Github-user-name>:${ghPersonalAccessToken}@github.com/<Github-username>/<Github-repo-name>.git"]]
                    ]) 
                }  
            }
        }
        stage("Setup ML Environment") {
            steps {
                //check if ml environment exists
                script {
                    sh '''#!/usr/bin/env bash
                    conda create -y -n sbar-data python=3.10
                    source activate sbar-data
                    pip install -r requirements.txt
                    '''
                }
            }
        }
        stage("Data Monitoring") {
            steps {
                // data monitoring will run every <T> minutes 
                sh'''#!/usr/bin/env bash
                source activate sbar-data
                echo '[info] Running data monitor'
                echo '[info] Running data monitor'>log.txt
                python monitor_data.py>>log.txt
                '''
            }
        }
        stage("Update Search Bar Data") {
            steps {
                // Update data on search bar server
                script {
                    if (sh(returnStdout: true, script: 'cat log.txt | tail -n 1').contains("DATA UPDATE REQUIRED")) {
                        echo "[info] Triggering update-searchbar job"
                        currentBuild.result = 'SUCCESS'
                        build job: 'update-searchbar', parameters: []
                    } else {
                        echo "[info] No changes in data - aborting"
                        currentBuild.result = 'ABORTED'
                    }
                }
                
            }
        }
        stage("Sync stage with prod") {
            steps {
                // sync stage with prod
                script {
                    if (sh(returnStdout: true, script: 'cat log.txt | tail -n 1').contains("DATA UPDATE REQUIRED")) {
                        echo "[info] Syncing stage with prod"
                        sh '''#!/usr/bin/env bash
                        git stash
                        git checkout stage
                        git pull origin stage --rebase
                        git pull origin prod --rebase
                        git push origin stage
                        '''
                    } else {
                        echo "[info] No changes in data - aborting"
                        currentBuild.result = 'ABORTED'
                    }
                }
            }
        }
    }
}
```    

    
- Demo how to setup data monitor as a pipeline job
    - Avoid concurrent builds
    - Link the pipeline to a Github project: [https://github.com/Github-username/Github-repo-name/]
    - Define parameters:
        - GH_PERSONAL_ACCESS_TOKEN
    - Define build schedule
    - Link the pipeline to a jenkinsfile on Github repo
    - Test

# Multi-branch Pipeline in Jenkins

As per the latest updates, the GitHub Pull Request Builder plugin is deprecated, and it is recommended to use the GitHub plugin (GitHub SCM).

In newer versions of Jenkins, the GitHub Source plugin is already installed by default, so you don’t need to manually install the old Pull Request Builder plugin.

If the GitHub Pull Request Builder plugin is not available, you can simply create a third job as Multibranch Pipeline job in Jenkins, which natively supports GitHub webhooks, branch discovery, and PR builds without requiring the deprecated plugin.


**Creating MultiBranch Pipeline in Jenkins**

1. Configure Basic Details
    - Set Display Name of multibranch Pipeline

2. Set Branch Sources
    - Branch Sources → Add Source → GitHub

    - From the dropdown, choose GitHub. Select your GitHub credentials which you created earlier.

    - Repository HTTPS URL
    https://github.com/Github-username/Github-repo-name.git


    - Click Validate to confirm access.

3. Configure Behaviors

    - In Discover branches options, configure this:
        - Strategy: All branches
    
    - Discover pull requests from origin
        - Strategy:
            - Merging the pull request with the current target branch revision


4. Property Strategy (Optional)

    - Select All branches get the same properties
    - You can add properties such as build retention, environment variables, etc.

5. Build Configuration

    - Keep the Mode as Jenkinsfile

    - Set Script Path
        - If your Jenkinsfile is inside a folder:
            - jenkinsfiles/code_monitor

    (Modify the path based on your repo structure.)

6. Scan Repository Triggers

    - Enable:
    - Periodically if not otherwise run.
    This ensures Jenkins rescans your repo for new branches or PRs.


7. Save Configuration

    - Click: Save (or Apply → Save)
    - Jenkins will automatically start scanning the GitHub repository, detect all branches and PRs, and create jobs for each.



### Job 3: Code monitor

Triggered by PR: Whenever there is a code change, this job will test and validate:

- Type: Pipeline Job
- Trigger: New Pull Request or updates on an existing Pull Request


```groovy
pipeline {
    agent any

    environment {
        PATH = "$WORKSPACE/miniconda/bin:$PATH"
        GITHUB_REPO = "https://github.com/Github-username/Github-repo-name.git"
    }

    stages {

        stage('Repos') {
            steps {
                cleanWs(deleteDirs: true, notFailBuild: true, patterns: [[pattern: '*', type: 'INCLUDE']])

                script {
                    def srcBranch = env.CHANGE_BRANCH ?: env.BRANCH_NAME
                    def baseBranch = env.CHANGE_TARGET ?: "stage"

                    echo "[info] Pull Request Source Branch: ${srcBranch}"
                    echo "[info] Pull Request Target Branch: ${baseBranch}"
                    echo "[info] Current Branch: ${env.BRANCH_NAME}"
                    echo "[info] Pull Request ID: ${env.CHANGE_ID ?: 'N/A'}"
                    echo "[info] Pull Request Title: ${env.CHANGE_TITLE ?: 'N/A'}"

                    // Checkout target branch
                    checkout([
                        $class: 'GitSCM',
                        branches: [[name: "origin/${baseBranch}"]],
                        userRemoteConfigs: [[credentialsId: "github-credential", url: "${GITHUB_REPO}"]]
                    ])
                }

                sh '''
                    echo '[info] Creating backup of current stage/prod data and model'
                    rm -rf temp_ml || echo "[info] temp_ml not found — skipping"
                    mkdir -p temp_ml
                    cp data/project_mappings.csv temp_ml/project_mappings.csv || true
                    cp output/search.index temp_ml/search.index || true
                '''

                script {
                    def srcBranch = env.CHANGE_BRANCH ?: env.BRANCH_NAME
                    def baseBranch = env.CHANGE_TARGET ?: "stage"

                    checkout([
                        $class: 'GitSCM',
                        branches: [[name: "origin/${srcBranch}"]],
                        userRemoteConfigs: [[credentialsId: "github-credential", url: "${GITHUB_REPO}"]]
                    ])

                    sh "git pull origin ${srcBranch} --rebase"
                    sh "git checkout ${baseBranch} || git checkout -b ${baseBranch} origin/${baseBranch}"
                    sh "git reset --hard origin/${baseBranch}"
                    sh "git merge origin/${srcBranch} --no-edit"
                }
            }
        }

        stage("Setup ML Environment") {
            steps {
                sh '''
                    bash -c "
                    echo '[info] Setting up ML environment'
                    if conda env list | grep -q sbar-code; then
                        echo '[info] Environment exists, updating...'
                        source activate sbar-code
                        pip install -r requirements.txt
                    else
                        echo '[info] Creating new environment...'
                        conda create -y -n sbar-code python=3.10
                        source activate sbar-code
                        pip install -r requirements.txt
                    fi
                    "
                '''
            }
        }

        stage("Functional Tests") {
            steps {
                sh '''
                    bash -c "source activate sbar-code && python -m unittest discover -s test -p 'test*.py'"
                '''
            }
        }

        stage("Build Search Index") {
            steps {
                sh '''
                    bash -c "source activate sbar-code && \
                     echo '[info] Before running engine.py' > log.txt && \
                     wc -l temp_ml/project_mappings.csv >> log.txt 2>&1 || echo 'temp backup not found' >> log.txt && \
                     wc -l data/project_mappings.csv >> log.txt && \
                     echo '[info] Running engine.py ...' && \
                     python engine.py >> log.txt && \
                     echo '[info] After running engine.py' >> log.txt && \
                     wc -l temp_ml/project_mappings.csv >> log.txt 2>&1 || echo 'temp backup not found' >> log.txt && \
                     wc -l data/project_mappings.csv >> log.txt"
                '''
            }
        }

        stage("Push Changes to Stage") {
            steps {
                script {
                    sh '''
                        bash -c "source activate sbar-code && python validate_changes.py >> log.txt"
                    '''

                    if (sh(returnStdout: true, script: "cat log.txt | tail -n 1")
                        .contains("CHANGE VALIDATION: SUCCESS")) {

                        echo "[info] Changes validated successfully, merging into stage"

                        def msg = env.CHANGE_TITLE ?
                            "[jenkins-server autocommit] JenkinsMerge :: ${env.CHANGE_TITLE}->#${env.CHANGE_ID}" :
                            "[jenkins-server autocommit] JenkinsMerge :: ${env.BRANCH_NAME}"

                        sh "git add ."
                        sh "git commit -m \"${msg}\" || true"

                        withCredentials([usernamePassword(
                            credentialsId: "github-credentials",
                            usernameVariable: 'GIT_USER',
                            passwordVariable: 'GIT_TOKEN'
                        )]) {
                            sh """
                                git config --global user.email 'jenkins-ci@yourdomain'
                                git config --global user.name "${GIT_USER}"
                                git remote set-url origin https://${GIT_USER}:${GIT_TOKEN}@github.com/Github-user-name/Github-repo-name.git
                                git push origin stage
                            """
                        }
                    } else {
                        echo "[info] No valid changes detected. Aborting deployment."
                        currentBuild.result = 'ABORTED'
                    }
                }
            }
        }

        stage("Deploy Changes to Production") {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: "github-credentials",
                    usernameVariable: 'GIT_USER',
                    passwordVariable: 'GIT_TOKEN'
                )]) {
                    sh """
                        git checkout prod
                        git pull origin prod --rebase
                        git merge stage --no-edit
                        git push origin prod
                        echo '[info] Triggering deploy to search bar server'
                    """
                }
                build job: 'update-searchbar', parameters: []
            }
        }
    }
}
```
- Demo: How to Configure the Code Monitor Pipeline in Jenkins
- Configure Jenkins integration with GitHub via Webhooks:
    - http://JenkinsEC2-Public-IPv4-address:8080/ghprbhook (Don't use this webhook as Github Pull Request Builder Plugin is deprecated)
    - http://JenkinsEC2-Public-IPv4-address:8080/github-webhook/

- Enable “Avoid concurrent builds” to prevent overlapping runs.
- Link the Pipeline job to the GitHub project: https://github.com/Github-username/Github-repo-name/

- Define the required parameter:
GH_PERSONAL_ACCESS_TOKEN
- Point the job to the pipeline file in the repo:
- jenkinsfiles/code_monitor

Test with the full setup end-to-end.

## Concluding Tests

1. Synthetic data
2. Code change
3. Check jenkins jobs
4. Check logs on searchbar app server
5. Check github merge reports