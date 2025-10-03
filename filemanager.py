#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import requests
import socket
from urlparse import urlparse
from threading import Thread
from Queue import Queue

requests.packages.urllib3.disable_warnings()

class Worker(Thread):
    def __init__(self, tasks):
        super(Worker, self).__init__()
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try:
                func(*args, **kargs)
            except Exception as e:
                print e
            finally:
                self.tasks.task_done()

class ThreadPool:
    def __init__(self, num_threads):
        self.tasks = Queue(num_threads)
        for _ in range(num_threads):
            Worker(self.tasks)

    def add_task(self, func, *args, **kargs):
        self.tasks.put((func, args, kargs))

    def wait_completion(self):
        self.tasks.join()

def main(target):
    # Normalisasi URL
    if "://" not in target:
        target = "http://" + target
    target = target.rstrip('/')
    base_host = urlparse(target).netloc

    headers = {
        'User-Agent':
        'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:73.0)'
    }
    # Urutan endpoint yang akan dicek
    paths = ['/laravel-filemanager', '/filemanager', '/file-manager']

    for path in paths:
        full_url = target + path

        try:
            # Follow redirect, ambil full body & final URL
            resp = requests.get(
                full_url,
                headers=headers,
                timeout=5,
                verify=False,
                allow_redirects=True
            )
        except Exception as e:
            # Jika timeout atau error koneksi, lanjut ke path berikutnya
            continue

        # Cek apakah server mengembalikan 200 dan domain sama
        final = urlparse(resp.url)
        if resp.status_code == 200 and final.netloc == base_host:
            body = resp.text

            # Pastikan body memuat indikator Laravel File Manager
            if ('<title>File Manager</title>' in body
                or '/vendor/laravel-filemanager/' in body):
                print '[OK!] %s%s' % (target, path)
                with open('filemanager.txt', 'a') as out:
                    out.write(full_url + "\n")
                return

    # Jika semua path gagal
    print '\033[91m[BAD] %s\033[00m' % target

if __name__ == '__main__':
    print("""
         filemanager scanner
    """)
    targets = open(raw_input("Ips List .txt: "), 'r').read().splitlines()
    threads = int(raw_input("Thread: "))
    pool = ThreadPool(threads)

    for host in targets:
        pool.add_task(main, host)

    pool.wait_completion()
