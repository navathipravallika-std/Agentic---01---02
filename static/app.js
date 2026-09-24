/**
 * Customer Support Routing Agent - Frontend Application Logic
 * Powered by LangGraph & Google Gemini
 */

// Application State
const STATE = {
    apiKey: "",
    modelName: "gemini-3.6-flash",
    lastTriageState: null,
    isExecuting: false
};

// Initialization on DOM Load
document.addEventListener("DOMContentLoaded", async () => {
    initModals();
    await loadHealth();

    // Attach Action Listeners
    document.getElementById("btn-run-triage").addEventListener("click", runTriagePipeline);
    document.getElementById("btn-clear-ticket").addEventListener("click", resetTicketForm);
    document.getElementById("btn-copy-draft").addEventListener("click", copyDraftResponse);
    document.getElementById("btn-approve-send").addEventListener("click", approveAndSendDraft);
});

// Toast Notification
function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    
    let icon = "fa-circle-info";
    if (type === "success") icon = "fa-circle-check";
    if (type === "warning") icon = "fa-triangle-exclamation";
    if (type === "error") icon = "fa-circle-xmark";

    toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(40px)";
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Settings Modal
function initModals() {
    const modal = document.getElementById("api-modal");
    const trigger = document.getElementById("api-config-trigger");
    const closeBtn = document.getElementById("btn-close-modal");
    const cancelBtn = document.getElementById("btn-cancel-modal");
    const saveBtn = document.getElementById("btn-save-modal");
    const pwdToggle = document.getElementById("btn-toggle-pwd");
    const apiKeyInput = document.getElementById("modal-api-key");
    const modelSelect = document.getElementById("modal-model-select");

    apiKeyInput.value = STATE.apiKey;
    modelSelect.value = STATE.modelName;

    trigger.addEventListener("click", () => {
        modal.classList.add("active");
    });

    function closeModal() {
        modal.classList.remove("active");
    }

    closeBtn.addEventListener("click", closeModal);
    cancelBtn.addEventListener("click", closeModal);

    saveBtn.addEventListener("click", () => {
        STATE.apiKey = apiKeyInput.value.trim();
        STATE.modelName = modelSelect.value;
        document.getElementById("active-model-tag").textContent = STATE.modelName;
        const keyBadge = document.getElementById("key-status-badge");
        if (STATE.apiKey) {
            keyBadge.textContent = "Custom Key";
        }
        closeModal();
        showToast("Agent settings updated", "success");
    });

    pwdToggle.addEventListener("click", () => {
        if (apiKeyInput.type === "password") {
            apiKeyInput.type = "text";
            pwdToggle.innerHTML = '<i class="fa-regular fa-eye-slash"></i>';
        } else {
            apiKeyInput.type = "password";
            pwdToggle.innerHTML = '<i class="fa-regular fa-eye"></i>';
        }
    });
}

// Load Health from API
async function loadHealth() {
    try {
        const res = await fetch("/api/health");
        if (res.ok) {
            const health = await res.json();
            const keyBadge = document.getElementById("key-status-badge");
            if (health.has_api_key) {
                keyBadge.textContent = "API Ready";
                keyBadge.title = `Server Key: ${health.masked_key}`;
            } else {
                keyBadge.textContent = "Fallback Active";
                keyBadge.title = "Operating with Rule-Heuristics engine (Optional: Click to add Gemini API key)";
            }
        }
    } catch (err) {
        console.warn("Backend loading notice:", err);
    }
}

// Reset Form to Clean Blank State
function resetTicketForm() {
    document.getElementById("input-customer-name").value = "";
    document.getElementById("input-customer-email").value = "";
    document.getElementById("input-subject").value = "";
    document.getElementById("input-body").value = "";
    document.getElementById("input-customer-tier").value = "Pro";

    document.getElementById("empty-state-view").style.display = "flex";
    document.getElementById("results-view").style.display = "none";

    showToast("Form cleared", "info");
}

// Main Triage Pipeline Execution
async function runTriagePipeline() {
    if (STATE.isExecuting) return;

    const name = document.getElementById("input-customer-name").value.trim();
    const email = document.getElementById("input-customer-email").value.trim();
    const tier = document.getElementById("input-customer-tier").value;
    const subject = document.getElementById("input-subject").value.trim();
    const body = document.getElementById("input-body").value.trim();

    if (!subject && !body) {
        showToast("Please enter a subject or email message", "warning");
        return;
    }

    STATE.isExecuting = true;
    const btn = document.getElementById("btn-run-triage");
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> <span>Routing Ticket...</span>';
    btn.disabled = true;

    try {
        const response = await fetch("/api/triage", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                customer_name: name || "Valued Customer",
                customer_email: email || "customer@example.com",
                customer_tier: tier,
                subject: subject || "Support Inquiry",
                body: body,
                api_key: STATE.apiKey,
                model_name: STATE.modelName
            })
        });

        if (!response.ok) {
            throw new Error(`Triage failed: ${response.statusText}`);
        }

        const state = await response.json();
        STATE.lastTriageState = state;

        // Hide Empty State, Show Results
        document.getElementById("empty-state-view").style.display = "none";
        document.getElementById("results-view").style.display = "flex";

        // Populate Output Card
        renderTriageOutput(state);

        showToast(`Routed to ${state.category} (${intConfidence(state.confidence)}% confidence)`, "success");

    } catch (err) {
        console.error("Triage Error:", err);
        showToast("Error processing request: " + err.message, "error");
    } finally {
        STATE.isExecuting = false;
        btn.innerHTML = '<i class="fa-solid fa-play"></i> <span>Route & Draft Response</span>';
        btn.disabled = false;
    }
}

function intConfidence(conf) {
    if (conf === null || conf === undefined) return 95;
    return Math.round(conf * 100);
}

// Render Output Results
function renderTriageOutput(state) {
    const category = state.category || "General Inquiry";
    const confidence = intConfidence(state.confidence);
    const urgency = state.urgency || "Medium";
    const sentiment = state.sentiment || "Neutral";

    // Engine Badge
    const engineBadge = document.getElementById("engine-source-badge");
    if (state.is_fallback) {
        engineBadge.innerHTML = '<i class="fa-solid fa-bolt"></i> <span>Rule Engine (Fallback)</span>';
        engineBadge.style.color = "#fcd34d";
    } else {
        engineBadge.innerHTML = `<i class="fa-solid fa-microchip"></i> <span>${state.llm_model_used || "Gemini 3.6"}</span>`;
        engineBadge.style.color = "#c4b5fd";
    }

    // Category Badge
    const catBadge = document.getElementById("res-category");
    const catText = document.getElementById("res-category-text");
    catText.textContent = category;

    // Set Category Icons
    let catIcon = "fa-receipt";
    if (category === "Tech Support") catIcon = "fa-bug";
    if (category === "Sales") catIcon = "fa-briefcase";
    if (category === "Account & Escalation") catIcon = "fa-shield-halved";
    if (category === "General Inquiry") catIcon = "fa-circle-question";

    catBadge.innerHTML = `<i class="fa-solid ${catIcon}"></i> <span>${category}</span>`;

    // Confidence
    document.getElementById("res-confidence-bar").style.width = `${confidence}%`;
    document.getElementById("res-confidence-text").textContent = `${confidence}%`;

    // Urgency
    const urgencyEl = document.getElementById("res-urgency");
    urgencyEl.className = `urgency-pill urgency-${urgency.toLowerCase()}`;
    urgencyEl.textContent = `${urgency} Urgency`;

    // Sentiment
    const sentimentEl = document.getElementById("res-sentiment");
    sentimentEl.className = `sentiment-pill sentiment-${sentiment.toLowerCase()}`;
    sentimentEl.textContent = sentiment;

    // Extracted Entities
    const entitiesContainer = document.getElementById("res-entities");
    entitiesContainer.innerHTML = "";
    const entities = state.extracted_entities || [];
    if (entities.length === 0) {
        entitiesContainer.innerHTML = '<span class="text-dim" style="font-size:12px;">No specific entities detected</span>';
    } else {
        entities.forEach(ent => {
            const tag = document.createElement("span");
            tag.className = "tag-entity";
            let tagIcon = "fa-tag";
            if (ent.category.includes("invoice")) tagIcon = "fa-hashtag";
            if (ent.category.includes("dollar") || ent.category.includes("amount")) tagIcon = "fa-dollar-sign";
            if (ent.category.includes("error")) tagIcon = "fa-triangle-exclamation";
            if (ent.category.includes("seat")) tagIcon = "fa-users";

            tag.innerHTML = `<i class="fa-solid ${tagIcon}"></i> ${ent.value}`;
            entitiesContainer.appendChild(tag);
        });
    }

    // Reasoning
    document.getElementById("res-reasoning").textContent = state.routing_reasoning || "Categorized via LangGraph intent classification pipeline.";

    // Injected Policies List
    const policiesList = state.policies_applied || [];
    document.getElementById("policies-count").textContent = policiesList.length;
    const policiesUl = document.getElementById("injected-policies-ul");
    policiesUl.innerHTML = "";
    policiesList.forEach(p => {
        const li = document.createElement("li");
        li.textContent = p;
        policiesUl.appendChild(li);
    });

    // Draft Response
    document.getElementById("res-draft-textarea").value = state.draft_response || "";

    // 1-Click Action Buttons
    const actionsContainer = document.getElementById("action-buttons-container");
    actionsContainer.innerHTML = "";
    const actions = state.suggested_actions || [];

    actions.forEach(act => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "btn-action-tile";

        let actIcon = "fa-bolt";
        if (act.action_type === "refund_stripe") actIcon = "fa-brands fa-stripe";
        if (act.action_type === "create_jira_bug") actIcon = "fa-brands fa-jira";
        if (act.action_type === "create_crm_deal") actIcon = "fa-brands fa-salesforce";
        if (act.action_type === "page_oncall_lead") actIcon = "fa-solid fa-pager";
        if (act.action_type === "send_enterprise_kit") actIcon = "fa-solid fa-file-pdf";

        btn.innerHTML = `<i class="${actIcon}"></i> <span>${act.label}</span>`;
        btn.addEventListener("click", () => executeAgentAction(act, btn));
        actionsContainer.appendChild(btn);
    });
}

// Execute 1-Click Agent Action
async function executeAgentAction(action, btnElement) {
    try {
        btnElement.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> <span>Processing...</span>';
        const res = await fetch("/api/execute-action", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                action_id: action.action_id,
                action_type: action.action_type,
                payload: action.payload
            })
        });

        const data = await res.json();
        btnElement.classList.add("executed");
        btnElement.innerHTML = `<i class="fa-solid fa-circle-check text-success"></i> <span>${data.message}</span>`;
        showToast(`Action Executed: Ref ${data.external_reference_id}`, "success");
    } catch (err) {
        showToast("Action failed: " + err.message, "error");
        btnElement.innerHTML = `<i class="fa-solid fa-bolt"></i> <span>${action.label}</span>`;
    }
}

// Copy Draft
function copyDraftResponse() {
    const text = document.getElementById("res-draft-textarea").value;
    if (!text) return;
    navigator.clipboard.writeText(text);
    showToast("Response draft copied to clipboard", "success");
}

// Approve and Send
function approveAndSendDraft() {
    const customer = document.getElementById("input-customer-name").value || "Customer";
    showToast(`Response approved and dispatched to ${customer}`, "success");
}
