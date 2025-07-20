import redis
import json
import time

# 连接到Redis
r = redis.Redis(host='localhost', port=6379, db=0)

# 获取所有Redis键
all_keys = r.keys('*')
print(f"所有Redis键: {[k.decode() for k in all_keys]}")

# 获取所有任务元数据的键
task_keys = r.keys('celery-task-meta-*')
print(f"\n找到 {len(task_keys)} 个任务元数据键")

# 打印每个任务的状态和详细信息
for key in task_keys:
    value = r.get(key)
    data = json.loads(value)
    task_id = key.decode().replace('celery-task-meta-', '')
    status = data.get('status')
    result = data.get('result', {})
    
    print(f"\n任务详情:")
    print(f"任务ID: {task_id}")
    print(f"状态: {status}")
    
    # 检查任务是否处于PROGRESS状态
    if status == 'PROGRESS':
        print(f"进度百分比: {result.get('progress', '未知')}%")
        print(f"当前步骤: {result.get('current_step', '未知')}")
    elif status == 'SUCCESS':
        print(f"完成信息:")
        if isinstance(result, dict):
            print(f"  任务ID: {result.get('task_id', '未知')}")
            print(f"  状态: {result.get('status', '未知')}")
            print(f"  下载时间: {result.get('download_time', '未知')} 秒")
            print(f"  视频路径: {result.get('video_path', '未知')}")
            print(f"  文件大小: {result.get('file_size', '未知')} 字节")
    elif status == 'FAILURE':
        print(f"错误信息: {result}")
    
    # 打印任务的TTL (生存时间)
    ttl = r.ttl(key)
    if ttl > 0:
        print(f"剩余生存时间: {ttl} 秒 (约 {ttl/3600:.2f} 小时)")
    elif ttl == -1:
        print("剩余生存时间: 永久")
    else:
        print("剩余生存时间: 已过期或不存在")
        
    print('-' * 50)