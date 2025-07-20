import requests
import json
import time

# 获取所有任务ID
def get_task_ids():
    import redis
    r = redis.Redis(host='localhost', port=6379, db=0)
    task_keys = r.keys('celery-task-meta-*')
    return [key.decode().replace('celery-task-meta-', '') for key in task_keys]

# 获取任务状态
def get_task_status(task_id):
    try:
        response = requests.get(f"http://localhost:8000/status/{task_id}")
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP错误: {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

# 主函数
def main():
    # 获取所有任务ID
    task_ids = get_task_ids()
    print(f"找到 {len(task_ids)} 个任务")
    
    # 对每个任务ID获取状态
    for task_id in task_ids:
        print(f"\n获取任务 {task_id} 的状态:")
        status = get_task_status(task_id)
        print(json.dumps(status, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()