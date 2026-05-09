# main.tf
terraform {
  backend "s3" {
    # Replace with a completely unique name (e.g., yourname-costguard-state-2026)
    bucket = "snm-costguard-state-2026" 
    key    = "prod/terraform.tfstate"
    region = "us-east-1"
  }
}
provider "aws" {
  region = "us-east-1" 
}

# 1. Security Group (Firewall)
resource "aws_security_group" "web_sg" {
  name        = "costguard_web_sg"
  description = "Allow HTTP and SSH traffic"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] 
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] 
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# 2. EC2 Instance
resource "aws_instance" "costguard_server" {
  ami           = "ami-0c7217cdde317cfec" # Ubuntu 22.04 LTS (us-east-1)
  instance_type = "t3.micro"
  key_name      = "costguard-key"
  
  vpc_security_group_ids = [aws_security_group.web_sg.id]

  # Cloud-init script that runs on first boot
  user_data = <<-EOF
              #!/bin/bash
              # Update and install Docker & Git
              apt-get update -y
              apt-get install docker.io git -y
              systemctl start docker
              systemctl enable docker

            #   # Clone your repository (REPLACE WITH YOUR ACTUAL GITHUB URL)
            #   git clone https://github.com/Sagar-N-Mutalik/cloud-cost-guard.git /home/ubuntu/app
            #   cd /home/ubuntu/app

            #   # Build the Docker image
            #   docker build -t costguard-app .

            #   # Run the Docker container
            #   # REPLACE the DATABASE_URL with your Neon DB connection string
            #   docker run -d -p 80:80 \
            #     -e DATABASE_URL="postgres://username:password@ep-cool-butterfly-123456.us-east-2.aws.neon.tech/neondb?sslmode=require" \
            #     costguard-app
              EOF

  tags = {
    Name = "CostGuard-Prod"
  }
}

# 3. Output the IP
output "ec2_public_ip" {
  value = aws_instance.costguard_server.public_ip
}