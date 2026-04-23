<script>
  export let title = "";
  export let subtitle = "";
  export let leftImage = "";
  export let rightImage = "";
</script>

<div class="header-banner">
  <div class="header-illustration left">
    <img src={leftImage} alt="Left Illustration" class="illustration-img" />
  </div>

  <div class="header-text-content">
    <h1 class="page-title"><span>{@html title}</span></h1>
    <p class="page-subtitle">{subtitle}</p>
  </div>

  <div class="header-illustration right">
    <img src={rightImage} alt="Right Illustration" class="illustration-img" />
  </div>
</div>

<style>
  .header-banner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background-color: #f9fafb;
    padding: 2rem;
    border-radius: 0.5rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  }

  .header-illustration {
    flex: 1;
    display: flex;
  }

  .header-illustration.left {
    justify-content: flex-start;
  }

  .header-illustration.right {
    justify-content: flex-end;
  }

  .illustration-img {
    max-height: 110px;
    object-fit: contain;
  }

  .header-text-content {
    flex: 2;
    margin: 0 1rem;
    text-align: center;
  }

  .page-title {
    font-size: 2.5rem;
    font-weight: 800;
    margin: 0 0 0.5rem 0;
    color: #1e293b;
  }

  .page-subtitle {
    font-size: 1.1rem;
    font-weight: 400;
    color: #64748b;
    margin: 0;
  }

  .text-blue {
    color: #2563eb;
  }
</style>