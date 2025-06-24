import copy
import asyncio
import tqdm


class ProgressBar:
    @staticmethod
    async def wait_tasks_with_tqdm(tasks, description=""):
        """
        按照给定的任务列表进行进度条的生成, 还可以进行任务的描述的添加
        :param tasks:  任务
        :param description: 任务的描述
        :return:
        """
        copied_tasks = copy.copy(tasks)
        task_length = len(copied_tasks)
        bar_format = '{desc}{percentage:3.0f}%|{bar}|{n_fmt}/{total_fmt}'
        with tqdm.tqdm(total=task_length, colour="green", ncols=97, postfix="", bar_format=bar_format) as pbar:
            pbar.set_description(description)
            while True:
                done, pending = await asyncio.wait(copied_tasks, return_when=asyncio.FIRST_COMPLETED)
                copied_tasks = list(pending)
                pbar.update(len(done))
                if len(pending) == 0:
                    break
