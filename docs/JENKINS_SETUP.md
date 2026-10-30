# Jenkins CI/CD setup

How to run the [Jenkinsfile](../Jenkinsfile) pipeline locally: Jenkins in Docker, deployment to Minikube.
Tested on Windows 10 with Docker Desktop; the commands work the same in a Linux/macOS shell
except where PowerShell is shown.

```
GitHub ──poll every 2 min──▶ Jenkins (container) ──/var/run/docker.sock──▶ host Docker engine
                                   │                                         ├── test image, Redis, smoke container
                                   └── kubectl ──https://minikube:8443──▶ Minikube node (container)
                                                                              └── namespace ai-sim
```

## Pipeline stages

| Stage | What it does |
|---|---|
| Checkout | Clones the repository, tags the build as `<build number>-<commit>` |
| Build test image | `docker build --target test` |
| Lint | `ruff check app tests` inside the test image |
| Unit tests | `pytest` inside the test image with a real Redis on a private Docker network; JUnit report published to Jenkins |
| Build image | `docker build --target runtime`, tagged `ai-sim-service:<build>-<commit>` and `:latest` |
| Smoke test | Starts the runtime image and runs [scripts/smoke_test.py](../scripts/smoke_test.py) (`/health`, `/api/v1/predict`) |
| Deploy to Minikube | Loads the image into Minikube, applies [k8s/](../k8s), waits for the rollout, repeats the smoke test inside a pod |

Temporary containers, the network and the test image are removed after every build.

## Prerequisites

- Docker Desktop (running)
- Minikube and kubectl, only for the deploy stage. On Windows: `winget install Kubernetes.minikube`
  (kubectl comes with Docker Desktop)

## 1. Start Jenkins

```bash
docker compose -f jenkins/docker-compose.yml up -d --build
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

Open http://localhost:8080 and paste the password. The required plugins are already in the image
([jenkins/plugins.txt](../jenkins/plugins.txt)), so choose **Select plugins to install → None**, then
create the admin user.

Check that Jenkins can use the host Docker engine:

```bash
docker exec jenkins docker version
```

## 2. Start Minikube and connect Jenkins to it

```bash
minikube start --driver=docker
docker network connect minikube jenkins
```

The Minikube node is a container named `minikube` on the same Docker engine. After
`docker network connect`, Jenkins reaches its API server at `https://minikube:8443`.

Create a kubeconfig for Jenkins with that address (PowerShell):

```powershell
kubectl config view --flatten --minify --context minikube |
  ForEach-Object { $_ -replace 'server: https://127\.0\.0\.1:\d+', 'server: https://minikube:8443' } |
  Set-Content -Encoding ascii jenkins-kubeconfig.yaml
```

Bash equivalent:

```bash
kubectl config view --flatten --minify --context minikube \
  | sed -E 's#server: https://127\.0\.0\.1:[0-9]+#server: https://minikube:8443#' > jenkins-kubeconfig.yaml
```

The file contains client certificates and is git-ignored. Test it from the Jenkins container:

```bash
docker cp jenkins-kubeconfig.yaml jenkins:/tmp/kubeconfig
docker exec jenkins kubectl --kubeconfig /tmp/kubeconfig get nodes
```

## 3. Add the kubeconfig credential

**Manage Jenkins → Credentials → System → Global credentials → Add Credentials**

- Kind: **Secret file**
- File: `jenkins-kubeconfig.yaml`
- ID: `minikube-kubeconfig`

## 4. Create the pipeline job

**New Item** → name `ai-sim-service` → **Pipeline** → OK, then in *Pipeline*:

- Definition: **Pipeline script from SCM**
- SCM: **Git**, Repository URL `https://github.com/YersinBerdikulov/ai-component-microservice.git`
- Branch: `*/master`
- Script Path: `Jenkinsfile`

Save and click **Build Now** once. The first build registers the `pollSCM` trigger and the `DEPLOY`
parameter from the Jenkinsfile; after that every new commit pushed to GitHub starts a build within two
minutes. Use **Build with Parameters** and untick `DEPLOY` to run CI only (no Minikube needed).

## 5. Check the deployment

```bash
kubectl -n ai-sim get pods,svc
minikube service ai-sim -n ai-sim --url     # opens a tunnel, then try <url>/docs
```

Optional: the LLM endpoints need an API key in the cluster:

```bash
kubectl -n ai-sim create secret generic ai-sim-secrets --from-env-file=.env
kubectl -n ai-sim rollout restart deployment/ai-sim
```

## Screenshots for the report

1. Job page → **Stage View** with all stages green (several builds)
2. Build → **Test Result** (33 tests passed)
3. Build → **Console Output** of *Deploy to Minikube* (rollout, smoke test in the pod, `kubectl get pods,svc`)

## Troubleshooting

| Symptom | Fix |
|---|---|
| `permission denied ... docker.sock` | The container must run as root (`user: root` in the compose file); recreate it with `up -d --build` |
| `Unable to connect to the server` / `no such host minikube` | Run `docker network connect minikube jenkins` again; the connection is lost when Minikube or the Jenkins container is recreated |
| Certificate errors after `minikube delete` | A new cluster has new certificates: regenerate the kubeconfig and update the credential |
| Pods stay in `ErrImageNeverPull` | The image was not loaded into the node. The pipeline uses `ctr images import` for containerd (Minikube 1.39+ default) and `docker load` for the Docker runtime; check with `docker exec minikube crictl images` |
| `Failed to connect to repository` | The repository must be public, or add GitHub credentials to the job |
