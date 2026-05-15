document.addEventListener('DOMContentLoaded', () => {
  const ipInput = document.getElementById('comfy-ip');
  const saveBtn = document.getElementById('save-comfy-ip');

  // Load current ComfyUI URL from the config endpoint
  fetch('/config')
    .then(r => r.json())
    .then(cfg => {
      const url = cfg?.comfy_ui?.url;
      if (url) {
        const ipPart = url.replace(/^https?:\/\//, '');
        if (ipInput) ipInput.value = ipPart;
        const labelEl = document.getElementById('comfyui-label');
        if (labelEl) labelEl.textContent = `ComfyUI (${ipPart})`;
      }
    })
    .catch(() => console.warn('config недоступен'));

  // Save new IP to server via the unified /config endpoint
  let currentConfig = {};
  // Fetch current config once and keep it for updates
  fetch('/config')
    .then(r => r.json())
    .then(cfg => { currentConfig = cfg; })
    .catch(() => console.warn('Не удалось загрузить config для сохранения ComfyUI URL'));

  if (saveBtn) {
    saveBtn.addEventListener('click', () => {
      const ip = ipInput?.value?.trim();
      if (!ip) return;
      const url = ip.startsWith('http') ? ip : `http://${ip}`;
      // Merge/comfy_ui URL into current config
      const updatedConfig = { ...currentConfig, comfy_ui: { ...(currentConfig.comfy_ui || {}), url } };
      fetch('/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updatedConfig)
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
        .catch(() => {
            // Покажем подсказку в UI рядом с полем ввода IP
            let errorElem = document.getElementById('config-error');
            if (!errorElem) {
              errorElem = document.createElement('div');
              errorElem.id = 'config-error';
              errorElem.style.color = 'red';
              errorElem.style.marginTop = '5px';
              const parent = document.querySelector('.comfy-ip-input');
              if (parent) parent.appendChild(errorElem);
            }
            errorElem.textContent = 'Сервер недоступен';
          });
    });
  }

  // Load combined dashboard data (status + tasks)
  fetch('/dashboard')
    .then(r => r.json())
    .then(data => {
      const status = data.status || {};
      const tasks = data.tasks || {};

      // Update status blocks
      const statusMapping = {
        'Алексей': 'status-aleksey',
        'Маришка': 'status-mariska',
        'OpenClaw': 'status-openclaw',
        'ComfyUI': 'status-comfyui'
      };
      Object.entries(statusMapping).forEach(([agentName, elementId]) => {
        const state = status[agentName] || 'offline';
        const el = document.getElementById(elementId);
        if (el) {
          el.textContent = state;
          el.className = 'status ' + state;
        }
      });

      // Render tasks using the same DOM structure as before
      document.querySelectorAll('.status-bar.tasks-bar .status-item').forEach(item => {
        const agent = item.querySelector('h2')?.innerText?.trim();
        const tasksDiv = item.querySelector('.tasks');
        if (!tasksDiv) return;
        // Очистим контейнер, чтобы при повторном обновлении не дублировать задачи
        tasksDiv.innerHTML = '';
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
            if (task.date) {
              const p = document.createElement('p');
              p.textContent = `Дата: ${task.date}`;
              block.appendChild(p);
            }
            if (task.durationMin !== undefined && task.durationMin !== null) {
              const p = document.createElement('p');
              p.textContent = `Длительность: ${task.durationMin} мин`;
              block.appendChild(p);
            }
            // Если есть ошибка, выводим её (красным цветом) только для нужных агентов
            if (task.error) {
              const p = document.createElement('p');
              p.textContent = `Ошибка: ${task.error}`;
              p.style.color = 'red';
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
    .catch(() => console.warn('dashboard endpoint недоступен'));

  // Auto‑refresh page every 30 seconds
  setInterval(() => location.reload(), 30000);
});

