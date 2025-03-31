import datetime
import json
import platform
import requests
from subprocess import Popen, PIPE

# dns解析用到的api
api = "http://api.ip33.com/dns/resolver"

# 待解析的域名
hosts = ["api.themoviedb.org", "image.tmdb.org", "www.themoviedb.org", "api.thetvdb.com", "webservice.fanart.tv", "raw.githubusercontent.com", "api.github.com", "github.com"]

# dns服务商
dnsProvider = ["156.154.70.1", "208.67.222.222"]

# host文件的位置
hostLocate = "/etc/hosts"

# Docker容器名称列表
docker_container_names = ["emby", "my_container2"]

# 批量ping
def pingBatch(ips):
    if ips is not None and type(ips) == list:
        for ip in ips[:]:
            result = pingIp(ip)
            if not result:
                ips.remove(ip)

# ping ip返回ip是否连通
def pingIp(ip) -> bool:
    try:
        ping_process = Popen(["ping", "-c", "1", ip], stdout=PIPE, stderr=PIPE)
        ping_output, ping_error = ping_process.communicate()
        if ping_process.returncode == 0:
            print(f"[√] IP:{ip}  可以ping通")
            return True
        else:
            print(f"[×] IP:{ip}  无法ping通")
            return False
    except Exception as e:
        print(f"Ping IP:{ip} 出错：{str(e)}")
        return False

# 返回host对应domain的解析结果列表
def analysis(domain, dns) -> list:
    params = {
        "domain": domain,
        "type": "A",
        "dns": dns
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.60"
    }
    try:
        response = requests.post(url=api, data=params, headers=headers)
        ipDics = json.loads(response.text)["record"]
        ips = [dic["ip"] for dic in ipDics]
        return ips
    except Exception as e:
        print("解析dns出错：")
        print(e)

# 写入host信息
def hostWritor(hostDic):
    platInfo = platform.platform().upper()
    if "LINUX" in platInfo:
        hostFile = "/etc/hosts"
    else:
        print("未能识别当前操作系统，且用户未指定host文件所在目录！")
        return

    origin = ""
    with open(hostFile, "r", encoding="utf-8") as f:
        flag = False
        for eachLine in f.readlines():
            if r"###start###" in eachLine:
                flag = True
            elif r"###end###" in eachLine:
                flag = False
            else:
                if not flag:
                    origin = origin + eachLine
        origin = origin.strip()
        origin += "\n###start###\n"
        for eachHost in hostDic:
            for eachIp in hostDic[eachHost]:
                origin += eachIp + "\t" + eachHost + "\n"
        origin += "###最后更新时间:%s###\n" % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        origin += "###end###\n"

    with open(hostFile, "w", encoding="utf-8") as f:
        f.write(origin)

    # 同步到Docker容器
    sync_to_docker_containers(hostDic)

def sync_to_docker_containers(hostDic):
    # 修改循环变量为容器名称
    for container_name in docker_container_names:
        try:
            # 使用容器名称代替ID
            result = Popen(["docker", "exec", container_name, "cat", "/etc/hosts"], stdout=PIPE, stderr=PIPE)
            output, error = result.communicate()
            if result.returncode != 0:
                print(f"获取容器 {container_name} 内hosts文件出错：", error.decode())
                continue

            container_hosts = output.decode().splitlines()
            new_hosts = []
            for eachHost in hostDic:
                for eachIp in hostDic[eachHost]:
                    new_hosts.append(f"{eachIp}\t{eachHost}")

            container_hosts = [line for line in container_hosts if not any(host in line for host in hostDic.keys())]

            final_hosts = container_hosts + new_hosts
            final_hosts_content = "\n".join(final_hosts)

            # 使用容器名称进行写入操作
            process = Popen(["docker", "exec", "-i", container_name, "sh", "-c", f"echo '{final_hosts_content}' > /etc/hosts"], stdout=PIPE, stderr=PIPE)
            process.communicate()
            if process.returncode != 0:
                print(f"更新容器 {container_name} 内hosts文件出错：", process.stderr.read().decode())
            else:
                print(f"成功更新容器 {container_name} 内的hosts文件")
        except Exception as e:
            print(f"同步到Docker容器 {container_name} 出错：{str(e)}")

if __name__ == '__main__':
    resultDic = {}
    for host in hosts:
        for dns in dnsProvider:
            records = analysis(host, dns)
            pingBatch(records)
            if records is not None and len(records) > 0:
                if host not in resultDic:
                    resultDic[host] = records
                else:
                    resultDic[host] += records
    hostWritor(resultDic)
