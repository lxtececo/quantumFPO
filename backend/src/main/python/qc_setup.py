from qiskit_ibm_runtime import QiskitRuntimeService
service = QiskitRuntimeService.save_account(
    token="CO0jCqStyxaQMUf4AhXngUMMGm6xhwc4BPX7Wg0pA91I", 
    instance="crn:v1:bluemix:public:quantum-computing:us-east:a/fc9062914596437592cd7dfe21fa74b6:ca32464e-0f9b-4b57-819a-dd2f2684ed83::",
    overwrite=True
    )
