# Data Governance Checklist

Every training record should have provenance and usage rights.

Required metadata:

- source
- license / ownership basis
- collection timestamp
- category
- language
- version
- quality score
- content hash

Before training:

- remove secrets and credentials
- remove duplicates and near-duplicates
- enforce license policy
- apply privacy/PII handling policy
- quarantine malformed or suspicious documents
- track dataset manifests immutably
- preserve deletion capability for enterprise data
