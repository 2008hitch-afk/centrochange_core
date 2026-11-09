# CAP037 explicit isolated provisioning

This testlab-only Dockerfile is the approved explicit provisioner for the CAP037 migration rehearsal. Build it with the clean, detached `centrochange_core` source-definition checkout as context and `Dockerfile.provisioned-rehearsal` as the Dockerfile. It is not part of the product deployment recipe and must never be cited as a CAP040 remediation.

The image installs only Builder and Healthcare at manifest pins, copies only the detached source-definition app, asserts both Git SHAs during build, and performs the normal app asset build. No container mutation after build is permitted.

The recipe writes the versioned socketio port bootstrap before Healthcare's asset build; Marley imports this setting while building its patient portal.

`BASE_IMAGE` defaults to the target manifest image. The only permitted alternate
value is the immutable image recorded by the detached CURRENT source-definition
checkout, used to construct the isolated pre-upgrade baseline.
