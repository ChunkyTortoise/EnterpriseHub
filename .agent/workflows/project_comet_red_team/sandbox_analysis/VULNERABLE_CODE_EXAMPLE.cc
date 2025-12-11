// VULNERABLE_CODE_EXAMPLE.cc
//
// This is a hypothetical, simplified C++ code snippet demonstrating a logic flaw
// similar to the one described in CVE-2025-4609.
//
// CONTEXT: This code runs in the privileged BROWSER process. It's an IPC message
// handler that is supposed to create a resource (like a file handle or a shared
// memory segment) and return it to a sandboxed RENDERER process.

#include <iostream>
#include <memory>

// A simple enum to define different types of resources the renderer can request.
enum class ResourceType {
    // A safe, sandboxed resource with limited permissions.
    kSafe,
    // A privileged resource (e.g., a handle to the browser process itself).
    // The renderer should NEVER be able to request this directly.
    kPrivileged
};

// Represents a generic OS resource handle.
class ResourceHandle {
public:
    ResourceType type;
    std::string name;

    ResourceHandle(ResourceType t, std::string n) : type(t), name(n) {}

    void Print() {
        std::cout << "Resource Handle: '" << name << "' (Type: "
                  << (type == ResourceType::kSafe ? "Safe" : "Privileged") << ")" << std::endl;
    }
};

// THE FLAW IS HERE
// This function in the BROWSER process is called when it receives an IPC message
// from a RENDERER process.
//
// The renderer can specify a `requested_type` and a `fallback_type`. The flawed
// logic is that if the `requested_type` is not available, it grants the
// `fallback_type` without re-validating its permissions.
std::unique_ptr<ResourceHandle> GetResource(ResourceType requested_type, ResourceType fallback_type) {
    std::cout << "[Browser Process] Received request for resource." << std::endl;

    // Simulate checking if the requested resource is available.
    bool is_resource_available = (requested_type == ResourceType::kSafe);

    if (is_resource_available) {
        std::cout << "[Browser Process] Requested resource is available. Granting." << std::endl;
        return std::make_unique<ResourceHandle>(requested_type, "safe_resource.tmp");
    } else {
        // VULNERABILITY: The developer assumes the fallback is always safe.
        // The browser fails to check if the `fallback_type` is kPrivileged.
        // A compromised renderer can request a non-existent resource and set
        // the fallback to `kPrivileged`, tricking the browser into giving it
        // a handle it should never have access to.
        std::cout << "[Browser Process] WARNING: Requested resource not available. Granting fallback." << std::endl;
        return std::make_unique<ResourceHandle>(fallback_type, "privileged_browser_process_handle");
    }
}

// This function simulates a compromised RENDERER process making a malicious request.
void SimulateCompromisedRenderer() {
    std::cout << "\n[Renderer Process] Attacker has control." << std::endl;
    std::cout << "[Renderer Process] Crafting malicious IPC message..." << std::endl;

    // We request a resource type that we know is not available (e.g., an invalid one).
    ResourceType malicious_request = (ResourceType)99; // An invalid type

    // We set the fallback to the privileged resource we want.
    ResourceType malicious_fallback = ResourceType::kPrivileged;

    std::cout << "[Renderer Process] Sending IPC to browser: request invalid type, but set fallback to Privileged." << std::endl;
    
    // The IPC message is sent, and the browser process calls GetResource.
    auto handle = GetResource(malicious_request, malicious_fallback);

    std::cout << "[Renderer Process] Received handle from browser!" << std::endl;
    handle->Print();

    if (handle->type == ResourceType::kPrivileged) {
        std::cout << "[Renderer Process] SUCCESS. Sandbox escape achieved. We now have a privileged handle." << std::endl;
    }
}

int main() {
    SimulateCompromisedRenderer();
    return 0;
}
