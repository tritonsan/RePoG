param(
  [string]$Region = 'us-east-1',
  [string]$StackName = 'repog-hosted-runtime',
  [string]$RepositoryName = 'repog-hosted-runtime',
  [Parameter(Mandatory = $true)][string]$SharedSecret,
  [Parameter(Mandatory = $true)][string]$GoldenWorkspaceZip,
  [Parameter(Mandatory = $true)][string]$GoldenBootstrap,
  [string]$SiteOrigin = 'https://repog-living-table.tritonsan.chatgpt.site'
)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$goldenWorkspacePath = (Resolve-Path -LiteralPath $GoldenWorkspaceZip).Path
$goldenBootstrapPath = (Resolve-Path -LiteralPath $GoldenBootstrap).Path
$accountId = aws sts get-caller-identity --query Account --output text
aws ecr describe-repositories --repository-names $RepositoryName --region $Region 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) { aws ecr create-repository --repository-name $RepositoryName --region $Region --image-scanning-configuration scanOnPush=true | Out-Null }
$registry = "$accountId.dkr.ecr.$Region.amazonaws.com"
aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin $registry | Out-Null
$tag = (git -C $projectRoot rev-parse --short HEAD).Trim()
$imageUri = "$registry/$RepositoryName`:$tag"
docker build -f (Join-Path $projectRoot 'runtime\hosted\Dockerfile') -t $imageUri $projectRoot
docker push $imageUri
aws cloudformation deploy --region $Region --stack-name $StackName --template-file (Join-Path $PSScriptRoot 'template.yaml') --capabilities CAPABILITY_IAM --parameter-overrides "RuntimeImageUri=$imageUri" "SharedSecret=$SharedSecret" "SiteOrigin=$SiteOrigin"
$workspaceBucket = aws cloudformation describe-stacks --region $Region --stack-name $StackName --query "Stacks[0].Outputs[?OutputKey=='WorkspaceBucketName'].OutputValue" --output text
aws s3 cp $goldenWorkspacePath "s3://$workspaceBucket/golden/workspace.zip" --region $Region --sse AES256
aws s3 cp $goldenBootstrapPath "s3://$workspaceBucket/golden/bootstrap.json" --region $Region --sse AES256 --content-type application/json
aws cloudformation describe-stacks --region $Region --stack-name $StackName --query 'Stacks[0].Outputs' --output table
