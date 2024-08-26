# libcapella 1.0.9

## Installing
```
$ pip install libcapella
```

Create Capella database:
```
database_name = "test-cluster"
project_name = "test-project"
email = 'john.doe@example.com'
config = CapellaConfig(profile="default")
org = CapellaOrganization(config)
project = CapellaProject(org, project_name, email)
database = CapellaDatabase(project, database_name)
builder = CapellaDatabaseBuilder("aws")
builder = builder.name(database_name)
builder = builder.description("Test cluster")
builder = builder.region("us-east-1")
builder = builder.service_group("4x16", 3, 256)
config = builder.build()
database.create(config)
```

## Credentials Directory
Automation for Capella leverages the v4 public API. To integrate the v4 API with `libcapella`, create an API key in the Capella UI and save it to a file named ```default-api-key-token.txt``` in a directory named ```.capella``` in your home directory. Add the email associated with your Capella account to the `credentials` file in the `default` section.
```
.capella
├── credentials
├── default-api-key-token.txt
├── project-api-key-token.txt
└── test-api-key-token.txt
```
Credentials file format:
```
[default]
api_host = cloudapi.cloud.couchbase.com
token_file = default-api-key-token.txt
account_email = john.doe@example.com

[project]
token_file = project-api-key-token.txt
```
