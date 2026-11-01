/* Copyright 2026 opamp.info; Licensed under the Apache License, Version 2.0. */
window.CredentialManagerFunctions = {
  create: function create(deps) {
    const element = function element(identifier) {
      return document.getElementById(identifier);
    };

    const status = function status(message) {
      element("status").textContent = message;
    };

    const escapeHtml = function escapeHtml(value) {
      return String(value).replace(/[&<>"']/g, function replaceCharacter(character) {
        return {
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          "\"": "&quot;",
          "'": "&#39;"
        }[character];
      });
    };

    const apiFetch = async function apiFetch(url, options) {
      const requestOptions = options || {};
      return fetch(url, requestOptions);
    };

    const requestJson = async function requestJson(url, options) {
      const requestOptions = options || {};
      const response = await apiFetch(url, requestOptions);
      const payload = response.status === 204 ? {} : await response.json();
      if (!response.ok) {
        throw new Error(payload.error || "Request failed");
      }
      return payload;
    };

    const requestJsonIfOk = async function requestJsonIfOk(url, options) {
      const requestOptions = options || {};
      const response = await apiFetch(url, requestOptions);
      if (!response.ok) {
        return null;
      }
      return response.status === 204 ? {} : response.json();
    };

    const uploadFile = async function uploadFile(file) {
      const body = new FormData();
      body.append("file", file);
      return (
        await requestJson(
          "/svr-credentials-manager-service/api/v1/files",
          { method: "POST", body: body }
        )
      ).reference;
    };

    const readSectionDraft = function readSectionDraft() {
      return {
        enabled: element("connection-enabled").checked,
        destination_endpoint: element("destination-endpoint").value,
        headers_text: element("headers").value,
        certificate: {
          cert_file: element("certificate-ref").value,
          private_key_file: element("private-key-ref").value,
          ca_cert_file: element("certificate-ca-ref").value
        },
        tls: {
          ca_pem_file: element("tls-ca-ref").value,
          include_system_ca_certs_pool: element("system-ca").checked,
          insecure_skip_verify: element("skip-verify").checked,
          min_version: element("tls-min").value,
          max_version: element("tls-max").value,
          cipher_suites: element("cipher-suites").value.split(/\r?\n/).filter(Boolean)
        },
        proxy: {
          url: element("proxy-url").value,
          connect_headers_text: element("proxy-headers").value
        },
        other_settings_text: element("other-settings").value
      };
    };

    const writeSectionDraft = function writeSectionDraft(sectionDraft) {
      const currentDraft = sectionDraft || {};
      document.querySelectorAll(".pem-selector").forEach(function resetFileSelector(fileInput) {
        fileInput.value = "";
      });
      element("connection-enabled").checked = currentDraft.enabled !== false;
      element("destination-endpoint").value = currentDraft.destination_endpoint || "";
      element("headers").value = currentDraft.headers_text || "";
      element("certificate-ref").value = currentDraft.certificate?.cert_file || "";
      element("private-key-ref").value = currentDraft.certificate?.private_key_file || "";
      element("certificate-ca-ref").value = currentDraft.certificate?.ca_cert_file || "";
      element("tls-ca-ref").value = currentDraft.tls?.ca_pem_file || "";
      element("system-ca").checked = Boolean(currentDraft.tls?.include_system_ca_certs_pool);
      element("skip-verify").checked = Boolean(currentDraft.tls?.insecure_skip_verify);
      element("tls-min").value = currentDraft.tls?.min_version || "";
      element("tls-max").value = currentDraft.tls?.max_version || "";
      element("cipher-suites").value = (currentDraft.tls?.cipher_suites || []).join("\n");
      element("proxy-url").value = currentDraft.proxy?.url || "";
      element("proxy-headers").value = currentDraft.proxy?.connect_headers_text || "";
      element("other-settings").value = currentDraft.other_settings_text || "";
    };

    const draftFromSection = function draftFromSection(section) {
      const currentSection = section || {};
      return {
        enabled: currentSection.enabled !== false,
        destination_endpoint: currentSection.destination_endpoint || "",
        headers_text: JSON.stringify(currentSection.headers || {}, null, 2),
        certificate: {
          cert_file: currentSection.certificate?.cert_file || "",
          private_key_file: currentSection.certificate?.private_key_file || "",
          ca_cert_file: currentSection.certificate?.ca_cert_file || ""
        },
        tls: {
          ca_pem_file: currentSection.tls?.ca_pem_file || "",
          include_system_ca_certs_pool: Boolean(
            currentSection.tls?.include_system_ca_certs_pool
          ),
          insecure_skip_verify: Boolean(currentSection.tls?.insecure_skip_verify),
          min_version: currentSection.tls?.min_version || "",
          max_version: currentSection.tls?.max_version || "",
          cipher_suites: currentSection.tls?.cipher_suites || []
        },
        proxy: {
          url: currentSection.proxy?.url || "",
          connect_headers_text: JSON.stringify(
            currentSection.proxy?.connect_headers || {},
            null,
            2
          )
        },
        other_settings_text: JSON.stringify(
          currentSection.other_settings || {},
          null,
          2
        )
      };
    };

    const sectionFromDraft = function sectionFromDraft(sectionDraft) {
      const currentDraft = sectionDraft || {};
      return {
        enabled: currentDraft.enabled !== false,
        destination_endpoint: currentDraft.destination_endpoint || "",
        headers: currentDraft.headers_text.trim()
          ? JSON.parse(currentDraft.headers_text)
          : {},
        certificate: {
          cert_file: currentDraft.certificate?.cert_file || "",
          private_key_file: currentDraft.certificate?.private_key_file || "",
          ca_cert_file: currentDraft.certificate?.ca_cert_file || ""
        },
        tls: {
          ca_pem_file: currentDraft.tls?.ca_pem_file || "",
          include_system_ca_certs_pool: Boolean(
            currentDraft.tls?.include_system_ca_certs_pool
          ),
          insecure_skip_verify: Boolean(currentDraft.tls?.insecure_skip_verify),
          min_version: currentDraft.tls?.min_version || "",
          max_version: currentDraft.tls?.max_version || "",
          cipher_suites: currentDraft.tls?.cipher_suites || []
        },
        proxy: {
          url: currentDraft.proxy?.url || "",
          connect_headers: currentDraft.proxy?.connect_headers_text.trim()
            ? JSON.parse(currentDraft.proxy.connect_headers_text)
            : {}
        },
        other_settings: currentDraft.other_settings_text.trim()
          ? JSON.parse(currentDraft.other_settings_text)
          : {}
      };
    };

    const readSection = function readSection() {
      return sectionFromDraft(readSectionDraft());
    };

    const writeSection = function writeSection(section) {
      writeSectionDraft(draftFromSection(section));
    };

      return {
        element: element,
        escapeHtml: escapeHtml,
        requestJson: requestJson,
        requestJsonIfOk: requestJsonIfOk,
        uploadFile: uploadFile,
        readSectionDraft: readSectionDraft,
        writeSectionDraft: writeSectionDraft,
      draftFromSection: draftFromSection,
      sectionFromDraft: sectionFromDraft,
        readSection: readSection,
        writeSection: writeSection,
        status: status,
        state: deps.state
      };
  }
};
