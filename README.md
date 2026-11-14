Student Management System
A cloud-hosted Student Management Website built with Python, Flask,
MySQL, and AWS. The application is hosted on an Ubuntu-based Amazon
EC2 instance. Amazon RDS for MySQL stores student and related records,
while Amazon S3 stores student profile images. Nginx receives HTTP
requests and forwards them to the Flask application. Boto3 is used by
Python to communicate with S3.
Technology Stack
  Technology / Service   Purpose
  Python                 Main programming language
Flask                  Web application framework
MySQL                  Relational database
SQLAlchemy             Database interaction
Amazon EC2             Cloud hosting
Ubuntu                 EC2 operating system
Nginx                  Web server and reverse proxy
Amazon RDS             Managed MySQL database
Amazon S3              Profile image storage
Boto3                  Python SDK for AWS
Git and GitHub         Source-code version control
Main Features
- Manage student records through a web interface.
- Upload and store student profile images in Amazon S3.
- Store student information in an Amazon RDS MySQL database.
- Host the Flask application on an Ubuntu EC2 instance.
- Use Nginx to receive web traffic and forward requests to Flask.
Architecture
                         Users
                           |
                        HTTP :80
                           |
                    Amazon EC2 (Ubuntu)
                           |
                         Nginx
                           |
                    Flask Application
                      /           \
                     /             \
          Amazon RDS (MySQL)    Amazon S3
          Student records       Profile images
The browser sends requests to the EC2 public address. Nginx forwards
requests to Flask. Flask reads and writes records in RDS and uses Boto3
to manage image objects in S3. The database stores the image object
key/reference; the image file itself is stored in S3.
Repository Structure
Student_Management/
├── app/
│   ├── models/
│   ├── routes/
│   ├── services/
│   │   └── s3_service.py
│   ├── templates/
│   ├── static/
│   └── __init__.py
├── deploy/
├── scripts/
│   ├── schema.sql
│   ├── init_db.py
│   ├── seed_db.py
│   ├── test_rds.py
│   └── test_s3.py
├── config.py
├── requirements.txt
├── run.py
└── .env.example
Check the repository for the exact current file list because deployment
files may change as the project is updated.
Local Setup
1. Clone the repository
git clone https://github.com/arjunsanthosh594/Student_Management.git
cd Student_Management
2. Create and activate a virtual environment
Ubuntu/Linux:
python3 -m venv venv
source venv/bin/activate
Windows PowerShell:
python -m venv venv
.\venv\Scripts\Activate.ps1
3. Install dependencies
pip install -r requirements.txt
4. Configure environment variables
Create a local .env file:
cp .env.example .env
On Windows, copy .env.example to .env using File Explorer or:
Copy-Item .env.example .env
Edit .env and enter the values required by the current config.py and
.env.example. Typical settings include:
DB_HOST=your-rds-endpoint
DB_PORT=3306
DB_NAME=student_management_db
DB_USER=your_database_username
DB_PASSWORD=your_database_password

AWS_REGION=your-aws-region
S3_BUCKET_NAME=your-s3-bucket-name
Do not commit real passwords, secret keys, or other credentials. Use the
exact variable names expected by the project configuration.
5. Initialize the database
The repository includes scripts/schema.sql and scripts/init_db.py.
Use the initialization method supported by the current project
configuration. The SQL schema can be executed against the configured
MySQL database using a MySQL client. Alternatively, if configured for
the target database, run:
python scripts/init_db.py
The database name must match the application configuration. The supplied
project schema uses student_management_db.
6. Run the application
python run.py
Use the host and port configured by the application. The deployment
configuration discussed for this project has Flask listening on
127.0.0.1:5000, suitable for access through an Nginx reverse proxy on
EC2.
AWS Deployment Summary
Amazon EC2
1. Launch an Ubuntu EC2 instance.
2. Configure the security group to allow SSH (TCP 22) from the
   administrator's IP and HTTP (TCP 80) for website access. Allow HTTPS
   (TCP 443) only if HTTPS is configured.
3. Connect to the instance using SSH and its key pair.
4. Install Python, pip, virtual-environment support, and Nginx.
5. Transfer or clone the application and install its dependencies.
6. Configure the application's .env file.
7. Run the Flask application and configure Nginx to proxy requests to
   the Flask listener.
Amazon RDS (MySQL)
1. Create an RDS database using the MySQL engine.
2. Configure its VPC and security group.
3. Allow inbound MySQL traffic (TCP 3306) from the EC2 security group.
4. Configure the RDS endpoint and database credentials in the
   application environment.
5. Initialize the schema and verify the database connection.
Avoid exposing the RDS database port to the entire internet. The
database should normally be private and accessible only from the
application server or other explicitly authorized sources.
Amazon S3
1. Create an S3 bucket in the required AWS region.
2. Keep the bucket private unless there is a documented reason for
   public access.
3. Configure the bucket name and AWS region in the application
   environment.
4. Give the EC2 instance an IAM role with only the S3 permissions
   required by the application.
5. Use the application's Boto3 service to upload and manage profile
   images.
The S3 service is located at app/services/s3_service.py. It supports
operations such as image upload, deletion, and generating presigned URLs
for image retrieval.
Security Considerations
- Never commit .env, database passwords, AWS secret keys, or private
  SSH keys.
- Keep the S3 bucket private and use controlled access, such as
  presigned URLs.
- Prefer an IAM role attached to EC2 instead of storing long-term AWS
  access keys on the server.
- Restrict SSH access to trusted administrator IP addresses.
- Allow RDS MySQL traffic only from the EC2 security group or other
  explicitly authorized sources.
- Open only the network ports required by the deployment.
- Use HTTPS in a production deployment and configure TLS certificates.
Testing and Verification
The repository includes scripts that can help test the AWS connections:
python scripts/test_rds.py
python scripts/test_s3.py
Verify the project requirements:
  Requirement                         Verification
  Website hosted on EC2               Open the EC2 public address in a
browser

  Web server configured               Check Nginx service and
configuration

  Flask connected to RDS              Run the RDS test and verify
database records

  Student details stored in RDS       Inspect MySQL tables after adding a
student

  Images stored in S3                 Upload a profile image and verify
the object in the bucket

  Images displayed on website         Open the relevant student/admin
page and confirm the image loads
Security groups configured          Review EC2 and RDS inbound rules
Important Notes
- The selected application stack is Python + Flask + Nginx; this
  README does not describe Gunicorn as part of the deployment.
- Flask's built-in development server is not hardened for production.
  For a production deployment, use a production-grade WSGI server
  behind Nginx and configure HTTPS, process supervision, logging, and
  monitoring.
- Commands and configuration values may need adjustment to match the
  current repository version and AWS resources.
- Never publish real AWS credentials or database passwords in this
  README.
