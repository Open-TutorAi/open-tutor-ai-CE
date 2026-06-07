<!-- src/lib/components/student/elements/EngagementChart.svelte -->

<script>
  import { onMount } from 'svelte';
  import { user } from '$lib/stores';
  import { getContext } from 'svelte';
  
  let engagement = null;
  let timeline = [];
  let alerts = [];
  let isLoading = true;
  let error = null;
  
  const i18n = getContext('i18n');
  
  onMount(async () => {
    try {
      const [engagementRes, timelineRes, alertsRes] = await Promise.all([
        fetch('/api/v1/dashboard/engagement?period_days=7', {
          headers: { 'Authorization': `Bearer ${$user.token}` }
        }),
        fetch('/api/v1/dashboard/engagement/timeline?days=7', {
          headers: { 'Authorization': `Bearer ${$user.token}` }
        }),
        fetch('/api/v1/dashboard/engagement/alerts', {
          headers: { 'Authorization': `Bearer ${$user.token}` }
        })
      ]);
      
      if (!engagementRes.ok || !timelineRes.ok || !alertsRes.ok) {
        throw new Error('Erreur de chargement des données');
      }
      
      engagement = await engagementRes.json();
      timeline = (await timelineRes.json()).timeline;
      alerts = (await alertsRes.json()).alerts;
      
    } catch (err) {
      error = err.message;
    } finally {
      isLoading = false;
    }
  });
  
  function trackPageView() {
    fetch('/api/v1/engagement/track?activity_type=page_view', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${$user.token}`
      }
    }).catch(() => {});
  }
</script>

{#if isLoading}
  <div class="engagement-skeleton">
    <div class="skeleton-header"></div>
    <div class="skeleton-chart"></div>
    <div class="skeleton-metrics"></div>
  </div>
{:else if error}
  <div class="error-state">
    ⚠️ {$i18n.t('Unable to load engagement data')}
  </div>
{:else if engagement}
  <div class="engagement-container">
    <!-- ALERTES -->
    {#if alerts.length > 0}
      <div class="alerts-section">
        {#each alerts as alert}
          <div class="alert alert-{alert.type} alert-priority-{alert.priority}">
            <div class="alert-content">
              <strong>{alert.title}</strong>
              <p>{alert.message}</p>
            </div>
            {#if alert.action}
              <a href={alert.actionLink} class="alert-action">
                {alert.action} →
              </a>
            {/if}
          </div>
        {/each}
      </div>
    {/if}
    
    <!-- SCORE GLOBAL -->
    <div class="score-card" 
         style="background: linear-gradient(135deg, {engagement.metrics.engagementScore >= 60 ? '#667eea' : '#764ba2'} 0%, {engagement.metrics.engagementScore >= 60 ? '#764ba2' : '#f093fb'} 100%)">
      <div class="score-header">
        <span class="score-label">{$i18n.t('Engagement Score')}</span>
        <span class="score-trend">{engagement.metrics.trend === 'up' ? '📈' : engagement.metrics.trend === 'down' ? '📉' : '➡️'} {engagement.metrics.trendPercentage}%</span>
      </div>
      <div class="score-value">{engagement.metrics.engagementScore}</div>
      <div class="score-level">{engagement.interpretation.level}</div>
      <p class="score-message">{engagement.interpretation.message}</p>
    </div>
    
    <!-- TIMELINE CHART -->
    <div class="timeline-section">
      <h4 class="timeline-title">{$i18n.t('Activity this week')}</h4>
      <div class="timeline-chart">
        {#each timeline as day}
          <div class="day-column">
            <div class="bar-container">
              <div 
                class="bar-fill" 
                style="height: {day.score}%; background: {day.color}"
                title="{day.timeSpent} min, {day.sessions} sessions"
              ></div>
            </div>
            <span class="day-label">{day.dayOfWeek}</span>
            <span class="day-date">{day.dayShort}</span>
            <span class="day-time">{day.timeSpent}m</span>
          </div>
        {/each}
      </div>
    </div>
    
    <!-- MÉTRIQUES DÉTAILLÉES -->
    <div class="metrics-grid">
      <div class="metric-card">
        <div class="metric-icon">⏱️</div>
        <div class="metric-value">{engagement.metrics.totalTimeSpentFormatted}</div>
        <div class="metric-label">{$i18n.t('Study time')}</div>
      </div>
      
      <div class="metric-card">
        <div class="metric-icon">✅</div>
        <div class="metric-value">{engagement.metrics.sessionsCompleted}/{engagement.metrics.sessionsStarted}</div>
        <div class="metric-label">{$i18n.t('Sessions completed')}</div>
        <div class="metric-sub">{engagement.metrics.sessionsCompletionRate}%</div>
      </div>
      
      <div class="metric-card">
        <div class="metric-icon">👆</div>
        <div class="metric-value">{engagement.metrics.totalClicks}</div>
        <div class="metric-label">{$i18n.t('Interactions')}</div>
      </div>
      
      <div class="metric-card">
        <div class="metric-icon">💬</div>
        <div class="metric-value">{engagement.metrics.feedbacksGiven}</div>
        <div class="metric-label">{$i18n.t('Feedbacks')}</div>
      </div>
      
      <div class="metric-card warning">
        <div class="metric-icon">⚠️</div>
        <div class="metric-value">{engagement.metrics.dropOffs}</div>
        <div class="metric-label">{$i18n.t('Drop-offs')}</div>
      </div>
      
      <div class="metric-card">
        <div class="metric-icon">👁️</div>
        <div class="metric-value">{engagement.metrics.pageViews}</div>
        <div class="metric-label">{$i18n.t('Page views')}</div>
      </div>
    </div>
  </div>
{/if}

<style>
  .engagement-container {
    display: flex;
    flex-direction: column;
    gap: 24px;
    margin-bottom: 32px;
    padding-top: 8px;
    overflow: visible;
  }
  
  /* ALERTES */
  .alerts-section {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  
  .alert {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    border-radius: 12px;
    gap: 16px;
  }
  
  .alert-success { background: #dcfce7; color: #166534; }
  .alert-info { background: #dbeafe; color: #1e40af; }
  .alert-warning { background: #fef3c7; color: #92400e; }
  .alert-encouragement { background: #f3e8ff; color: #6b21a8; }
  
  .alert-priority-high { border-left: 4px solid #ef4444; }
  .alert-priority-medium { border-left: 4px solid #f59e0b; }
  .alert-priority-low { border-left: 4px solid #10b981; }
  
  .alert-action {
    background: white;
    padding: 8px 16px;
    border-radius: 8px;
    text-decoration: none;
    font-weight: 600;
    white-space: nowrap;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }
  
  /* SCORE CARD */
  .score-card {
    padding: 32px;
    border-radius: 20px;
    color: white;
    text-align: center;
  }
  
  .score-header {
    display: flex;
    justify-content: space-between;
    font-size: 0.9rem;
    opacity: 0.9;
    margin-bottom: 16px;
  }
  
  .score-value {
    font-size: 4rem;
    font-weight: 800;
    line-height: 1;
    margin-bottom: 8px;
  }
  
  .score-level {
    font-size: 1.2rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 12px;
  }
  
  .score-message {
    font-size: 0.95rem;
    opacity: 0.95;
    margin: 0;
  }
  
  /* TIMELINE — CORRIGÉ ET NETTOYÉ */
  .timeline-section {
    background: white;
    padding: 32px 24px 24px 24px;   /* ← 32px en haut pour le titre */
    border-radius: 16px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    overflow: visible;
    position: relative;
  }
  
  .timeline-title {
    margin: 0 0 20px 0;
    color: #1e293b;
    font-size: 1.1rem;
    font-weight: 600;
    line-height: 1.5;
    padding-top: 4px;
    display: block;
    width: 100%;
  }
  
  .timeline-chart {
    display: flex;
    align-items: flex-end;
    justify-content: space-around;
    height: 200px;
    gap: 12px;
    padding-top: 8px;
  }
  
  .day-column {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
  }
  
  .bar-container {
    width: 100%;
    height: 160px;
    display: flex;
    align-items: flex-end;
    background: #f1f5f9;
    border-radius: 8px 8px 0 0;
    overflow: hidden;
  }
  
  .bar-fill {
    width: 100%;
    border-radius: 8px 8px 0 0;
    transition: height 0.8s ease-out;
    min-height: 4px;
  }
  
  .day-label {
    font-size: 0.8rem;
    font-weight: 600;
    color: #64748b;
  }
  
  .day-date {
    font-size: 0.7rem;
    color: #94a3b8;
  }
  
  .day-time {
    font-size: 0.75rem;
    color: #475569;
    font-weight: 500;
  }
  
  /* MÉTRIQUES */
  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 16px;
  }
  
  .metric-card {
    background: white;
    padding: 20px;
    border-radius: 16px;
    text-align: center;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    transition: transform 0.2s;
  }
  
  .metric-card:hover {
    transform: translateY(-4px);
  }
  
  .metric-card.warning {
    background: #fef2f2;
    border: 2px solid #fecaca;
  }
  
  .metric-icon {
    font-size: 2rem;
    margin-bottom: 8px;
  }
  
  .metric-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: #1e293b;
    line-height: 1;
  }
  
  .metric-label {
    font-size: 0.8rem;
    color: #64748b;
    margin-top: 4px;
  }
  
  .metric-sub {
    font-size: 0.85rem;
    color: #10b981;
    font-weight: 600;
    margin-top: 4px;
  }
  
  /* SKELETON */
  .engagement-skeleton {
    display: flex;
    flex-direction: column;
    gap: 24px;
  }
  
  .skeleton-header, .skeleton-chart, .skeleton-metrics {
    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
    background-size: 200% 100%;
    border-radius: 16px;
    animation: shimmer 1.5s infinite;
  }
  
  .skeleton-header { height: 200px; }
  .skeleton-chart { height: 240px; }
  .skeleton-metrics { height: 120px; }
  
  @keyframes shimmer {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
  }
  
  /* ERROR */
  .error-state {
    background: #fef2f2;
    border: 2px solid #fecaca;
    border-radius: 16px;
    padding: 24px;
    text-align: center;
    color: #991b1b;
  }
</style>