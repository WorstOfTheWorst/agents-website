// Load status and apply color classes
fetch('data/status.json')
  .then(r => r.json())
  .then(status => {
    const statusMapping = {
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
  .catch(() => console.warn('status.json недоступен'))

// Load recent tasks with human‑readable details
fetch('data/agents_tasks_detail_human.json')
  .then(r => r.json())
  .then(tasks => {
    document.querySelectorAll('.col').forEach(col => {
      const agent = col.querySelector('h2').innerText.trim();
      const tasksDiv = col.querySelector('.tasks');
      if (!tasksDiv) return;
      const container = document.createElement('div');
      const arr = tasks[agent] || [];
      arr.forEach(item => {
        const block = document.createElement('div');
        block.className = 'task-block';
        if (item.label) {
          const p = document.createElement('p');
          p.textContent = `Задача: ${item.label}`;
          block.appendChild(p);
        }
        if (item.status) {
          const p = document.createElement('p');
          p.textContent = `Статус: ${item.status}`;
          block.appendChild(p);
        }
        if (item.startedAt) {
          const p = document.createElement('p');
          p.textContent = `Время начала: ${item.startedAt}`;
          block.appendChild(p);
        }
        if (item.durationMin !== undefined && item.durationMin !== null) {
          const p = document.createElement('p');
          p.textContent = `Длительность: ${item.durationMin} мин`;
          block.appendChild(p);
        }
        container.appendChild(block);
        const sep = document.createElement('div');
        sep.className = 'task-sep';
        container.appendChild(sep);
      });
      if (arr.length === 0) {
        const placeholder = document.createElement('p');
        placeholder.textContent = '—';
        placeholder.className = 'placeholder';
        container.appendChild(placeholder);
      }
      tasksDiv.appendChild(container);
    });
  })
  .catch(() => console.warn('agents_tasks_detail_human.json недоступен'))

// Auto‑refresh page every 30 seconds to keep data fresh
setInterval(() => location.reload(), 30000);