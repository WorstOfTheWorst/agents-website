// Load ComfyUI IP from server file and prefill input + update label
document.addEventListener('DOMContentLoaded', () => {
  const ipInput = document.getElementById('comfy-ip');
  const saveBtn = document.getElementById('save-comfy-ip');

  // Prefill input and update label from server file
  fetch('/data/comfy_ip.json')
    .then(r => r.json())
    .then(cfg => {
      if (cfg.url) {
        const ipPart = cfg.url.replace(/^https?:\/\//, '');

        if (ipInput) {
          ipInput.value = ipPart;
        }

        const labelEl = document.getElementById('comfyui-label');
        if (labelEl) {
          labelEl.textContent = `ComfyUI (${ipPart})`;
        }
      }
    })
    .catch(() => console.warn('comfy_ip.json недоступен'));

  // Save new IP to server
  if (saveBtn) {
    saveBtn.addEventListener('click', () => {
      const ip = ipInput?.value?.trim();
      if (!ip) return;

      const url = ip.startsWith('http') ? ip : `http://${ip}`;

      fetch('/save_comfy_ip', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      })
        .then(r => {
          if (r.ok) {
            const labelEl = document.getElementById('comfyui-label');
            if (labelEl) labelEl.textContent = `ComfyUI (${ip})`;
            alert('IP сохранён');
          } else {
            alert('Ошибка сохранения');
          }
        })
        .catch(() => alert('Сервер недоступен'));
    });
  }
});

// Load status and apply color classes
fetch('data/status.json')
  .then(r => r.json())
  .then(status => {
    const statusMapping = {
      'Алексей': 'status-aleksey',
      'Маришка': 'status-mariska',
      'OpenClaw': 'status-openclaw',
      'ComfyUI': 'status-comfyui'
    };
    Object.entries(statusMapping).forEach(([agentName, elementId]) => {
      const state = status[agentName] || 'offline';
      const statusDiv = document.getElementById(elementId);
      if (statusDiv) {
        statusDiv.textContent = state;
        statusDiv.className = 'status ' + state;
      }
    });
  })
  .catch(() => console.warn('status.json недоступен'));

// Load recent tasks with human‑readable details
fetch('data/agents_tasks_detail_human.json')
  .then(r => r.json())
  .then(tasks => {
    // Iterate over each agent task section in the UI
    document.querySelectorAll('.status-bar.tasks-bar .status-item').forEach(item => {
      const agent = item.querySelector('h2')?.innerText?.trim();
      const tasksDiv = item.querySelector('.tasks');
      if (!tasksDiv) return;

      const container = document.createElement('div');
      const arr = tasks[agent] || [];

      if (arr.length === 0) {
        const placeholder = document.createElement('p');
        placeholder.textContent = '—';
        placeholder.className = 'placeholder';
        container.appendChild(placeholder);
      } else {
        arr.forEach(task => {
          const block = document.createElement('div');
          block.className = 'task-block';

          if (task.label) {
            const p = document.createElement('p');
            p.textContent = `Задача: ${task.label}`;
            block.appendChild(p);
          }
          if (task.status) {
            const p = document.createElement('p');
            p.textContent = `Статус: ${task.status}`;
            block.appendChild(p);
          }
          if (task.startedAt) {
            const p = document.createElement('p');
            p.textContent = `Время начала: ${task.startedAt}`;
            block.appendChild(p);
          }
          if (task.durationMin !== undefined && task.durationMin !== null) {
            const p = document.createElement('p');
            p.textContent = `Длительность: ${task.durationMin} мин`;
            block.appendChild(p);
          }

          container.appendChild(block);

          const sep = document.createElement('div');
          sep.className = 'task-sep';
          container.appendChild(sep);
        });
      }

      tasksDiv.appendChild(container);
    });
  })
  .catch(() => console.warn('agents_tasks_detail_human.json недоступен'));

// Auto‑refresh page every 30 seconds to keep data fresh
setInterval(() => location.reload(), 30000);