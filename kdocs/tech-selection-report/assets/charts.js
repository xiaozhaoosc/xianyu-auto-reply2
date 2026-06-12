(function() {
  var style = getComputedStyle(document.documentElement);
  var accent = style.getPropertyValue('--accent').trim() || '#2563eb';
  var accent2 = style.getPropertyValue('--accent2').trim() || '#0891b2';
  var ink = style.getPropertyValue('--ink').trim() || '#1a1a2e';
  var muted = style.getPropertyValue('--muted').trim() || '#6b7280';
  var rule = style.getPropertyValue('--rule').trim() || '#d1d5db';
  var bg2 = style.getPropertyValue('--bg2').trim() || '#f0f2f5';

  // --- Chart 1: Radar — 四语言适配度 ---
  var radarChart = echarts.init(document.getElementById('chart-radar'), null, { renderer: 'svg' });
  radarChart.setOption({
    animation: false,
    tooltip: { appendToBody: true },
    legend: {
      bottom: 0,
      textStyle: { color: ink, fontSize: 12 }
    },
    radar: {
      center: ['50%', '55%'],
      radius: '65%',
      indicator: [
        { name: 'Playwright', max: 5 },
        { name: 'ORM 能力', max: 5 },
        { name: '异步/并发', max: 5 },
        { name: 'AI SDK 生态', max: 5 },
        { name: '字符串处理', max: 5 },
        { name: '规则引擎', max: 5 },
        { name: '开发效率', max: 5 },
        { name: '类型安全', max: 5 }
      ],
      axisName: { color: muted, fontSize: 10 },
      splitArea: { areaStyle: { color: [bg2, 'transparent'] } },
      splitLine: { lineStyle: { color: rule } },
      axisLine: { lineStyle: { color: rule } }
    },
    series: [{
      type: 'radar',
      data: [
        {
          name: 'Python',
          value: [5, 4, 4, 5, 5, 2, 5, 2.5],
          lineStyle: { color: accent, width: 2 },
          areaStyle: { color: accent + '22' },
          itemStyle: { color: accent },
          symbol: 'circle',
          symbolSize: 6
        },
        {
          name: 'Java',
          value: [4, 5, 4.5, 3, 4, 5, 3, 5],
          lineStyle: { color: accent2, width: 2 },
          areaStyle: { color: accent2 + '22' },
          itemStyle: { color: accent2 },
          symbol: 'diamond',
          symbolSize: 6
        },
        {
          name: 'Go',
          value: [2.5, 3, 5, 2.5, 3, 2, 4, 4],
          lineStyle: { color: '#f59e0b', width: 2 },
          areaStyle: { color: '#f59e0b22' },
          itemStyle: { color: '#f59e0b' },
          symbol: 'triangle',
          symbolSize: 6
        },
        {
          name: 'Rust',
          value: [1, 2.5, 5, 1, 3, 2, 2.5, 5],
          lineStyle: { color: '#ef4444', width: 2 },
          areaStyle: { color: '#ef444422' },
          itemStyle: { color: '#ef4444' },
          symbol: 'rect',
          symbolSize: 6
        }
      ]
    }]
  });
  window.addEventListener('resize', function() { radarChart.resize(); });

  // --- Chart 2: Bar — 框架综合评分 ---
  var fwChart = echarts.init(document.getElementById('chart-framework'), null, { renderer: 'svg' });
  fwChart.setOption({
    animation: false,
    tooltip: {
      appendToBody: true,
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    legend: {
      bottom: 0,
      textStyle: { color: ink, fontSize: 12 }
    },
    grid: { left: 12, right: 12, top: 12, bottom: 48 },
    xAxis: {
      type: 'category',
      data: ['多终端', '代码生成', '安全体系', '技术栈\n现代化', '社区生态', '开源协议', '代码质量'],
      axisLabel: { color: muted, fontSize: 10 },
      axisLine: { lineStyle: { color: rule } },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      max: 5,
      interval: 1,
      axisLabel: { color: muted, fontSize: 10 },
      splitLine: { lineStyle: { color: rule } },
      axisLine: { show: false }
    },
    series: [
      {
        name: 'SmartAdmin',
        type: 'bar',
        data: [
          { value: 4.5, itemStyle: { color: accent } },
          { value: 4, itemStyle: { color: accent } },
          { value: 5, itemStyle: { color: accent } },
          { value: 5, itemStyle: { color: accent } },
          { value: 4, itemStyle: { color: accent } },
          { value: 5, itemStyle: { color: accent } },
          { value: 5, itemStyle: { color: accent } }
        ],
        barWidth: 22,
        emphasis: { itemStyle: { color: accent } }
      },
      {
        name: '若依',
        type: 'bar',
        data: [
          { value: 4.5, itemStyle: { color: accent2 } },
          { value: 4.5, itemStyle: { color: accent2 } },
          { value: 3, itemStyle: { color: accent2 } },
          { value: 3.5, itemStyle: { color: accent2 } },
          { value: 5, itemStyle: { color: accent2 } },
          { value: 5, itemStyle: { color: accent2 } },
          { value: 4, itemStyle: { color: accent2 } }
        ],
        barWidth: 22,
        emphasis: { itemStyle: { color: accent2 } }
      },
      {
        name: 'JeePlus',
        type: 'bar',
        data: [
          { value: 1.5, itemStyle: { color: '#f59e0b' } },
          { value: 5, itemStyle: { color: '#f59e0b' } },
          { value: 2, itemStyle: { color: '#f59e0b' } },
          { value: 3, itemStyle: { color: '#f59e0b' } },
          { value: 2, itemStyle: { color: '#f59e0b' } },
          { value: 2, itemStyle: { color: '#f59e0b' } },
          { value: 3, itemStyle: { color: '#f59e0b' } }
        ],
        barWidth: 22,
        emphasis: { itemStyle: { color: '#f59e0b' } }
      }
    ]
  });
  window.addEventListener('resize', function() { fwChart.resize(); });

  // --- Chart 3: Bar — JDK 推荐度 ---
  var jdkChart = echarts.init(document.getElementById('chart-jdk'), null, { renderer: 'svg' });
  jdkChart.setOption({
    animation: false,
    tooltip: {
      appendToBody: true,
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    legend: { show: false },
    grid: { left: 12, right: 40, top: 12, bottom: 32 },
    xAxis: {
      type: 'category',
      data: ['虚拟线程', '结构化并发', 'Boot 4\n兼容', '生态成熟度', '剩余支持', '综合推荐'],
      axisLabel: { color: muted, fontSize: 10 },
      axisLine: { lineStyle: { color: rule } },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      max: 5,
      interval: 1,
      axisLabel: { color: muted, fontSize: 10 },
      splitLine: { lineStyle: { color: rule } },
      axisLine: { show: false }
    },
    series: [
      {
        name: 'JDK 17',
        type: 'bar',
        data: [
          { value: 1.5, itemStyle: { color: '#94a3b8' } },
          { value: 0, itemStyle: { color: '#94a3b8' } },
          { value: 0, itemStyle: { color: '#94a3b8' } },
          { value: 5, itemStyle: { color: '#94a3b8' } },
          { value: 2.5, itemStyle: { color: '#94a3b8' } },
          { value: 2.5, itemStyle: { color: '#94a3b8' } }
        ],
        barWidth: 18,
        emphasis: { itemStyle: { color: '#94a3b8' } }
      },
      {
        name: 'JDK 21',
        type: 'bar',
        data: [
          { value: 5, itemStyle: { color: accent } },
          { value: 3, itemStyle: { color: accent } },
          { value: 5, itemStyle: { color: accent } },
          { value: 4.5, itemStyle: { color: accent } },
          { value: 4, itemStyle: { color: accent } },
          { value: 5, itemStyle: { color: accent } }
        ],
        barWidth: 18,
        emphasis: { itemStyle: { color: accent } }
      },
      {
        name: 'JDK 25',
        type: 'bar',
        data: [
          { value: 5, itemStyle: { color: accent2 } },
          { value: 5, itemStyle: { color: accent2 } },
          { value: 5, itemStyle: { color: accent2 } },
          { value: 3, itemStyle: { color: accent2 } },
          { value: 5, itemStyle: { color: accent2 } },
          { value: 4.5, itemStyle: { color: accent2 } }
        ],
        barWidth: 18,
        emphasis: { itemStyle: { color: accent2 } }
      }
    ]
  });
  window.addEventListener('resize', function() { jdkChart.resize(); });

  // --- Chart 4: Pie — 工作量分布 ---
  var wlChart = echarts.init(document.getElementById('chart-workload'), null, { renderer: 'svg' });
  wlChart.setOption({
    animation: false,
    tooltip: {
      appendToBody: true,
      trigger: 'item',
      formatter: '{b}: {c} 周 ({d}%)'
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
      textStyle: { color: muted, fontSize: 11 }
    },
    color: [accent, accent2, '#8b5cf6', '#f59e0b', '#22c55e', '#ef4444', '#94a3b8'],
    series: [{
      type: 'pie',
      radius: ['38%', '70%'],
      center: ['38%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 6,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: { show: false },
      emphasis: {
        label: { show: true, fontSize: 14, fontWeight: 'bold' }
      },
      data: [
        { value: 2, name: '基础设施搭建' },
        { value: 4, name: '数据模型迁移' },
        { value: 6, name: '管理后台页面' },
        { value: 8, name: '核心业务逻辑' },
        { value: 6, name: '移动端 H5/App' },
        { value: 4, name: 'Python 集成' },
        { value: 4, name: '联调测试' }
      ]
    }]
  });
  window.addEventListener('resize', function() { wlChart.resize(); });
})();