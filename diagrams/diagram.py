from diagrams import Cluster, Diagram
from diagrams.aws.storage import SimpleStorageServiceS3Bucket
from diagrams.k8s.group import NS
from diagrams.k8s.compute import Pod
from diagrams.k8s.storage import Vol
from diagrams.onprem.network import Traefik
from diagrams.onprem.vcs import Github
from diagrams.k8s.network import Ing, SVC

with Diagram("pet2cattle", show=False):
  ingress_controller = Traefik("ingress controller")
  git_repo = Github("posts")

  s3_bucket = SimpleStorageServiceS3Bucket("S3 bucket")

  with Cluster("pet2cattle namespace"):
    pet2cattle_blog = Pod("blog")
    pet2cattle_blog - [Vol("temporal data")]
    s3_bucket >> pet2cattle_blog

    pet2cattle_static = Pod("static content")
    pet2cattle_s3sync = Pod("s3sync")

    git_repo >> pet2cattle_s3sync

    pet2cattle_s3sync >> s3_bucket

    blog_ingress = Ing("blog content")
    static_ingress = Ing("static content")

    svc_blog = SVC("blog")
    svc_static = SVC("static")

    blog_ingress >> svc_blog >> pet2cattle_blog
    static_ingress >> svc_static >> pet2cattle_static

  
  ingress_controller >> blog_ingress
  ingress_controller >> static_ingress


    