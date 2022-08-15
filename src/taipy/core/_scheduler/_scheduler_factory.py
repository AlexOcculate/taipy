# Copyright 2022 Avaiga Private Limited
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
# an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
from importlib import util
from typing import Optional, Type

from taipy.config.config import Config
from taipy.config.exceptions.exceptions import ModeNotAvailable

from ..common._utils import _load_fct
from ..exceptions.exceptions import SchedulerNotBuilt
from ._abstract_scheduler import _AbstractScheduler
from ._dispatcher import _DevelopmentJobDispatcher, _JobDispatcher, _StandaloneJobDispatcher
from ._scheduler import _Scheduler


class _SchedulerFactory:

    _TAIPY_ENTERPRISE_MODULE = "taipy.enterprise"
    _TAIPY_ENTERPRISE_CORE_SCHEDULER_MODULE = _TAIPY_ENTERPRISE_MODULE + ".core._scheduler._scheduler"
    _TAIPY_ENTERPRISE_CORE_DISPATCHER_MODULE = _TAIPY_ENTERPRISE_MODULE + ".core._scheduler._dispatcher"
    __STANDADLONE_JOB_DISPATCHER_TYPE = "_StandaloneJobDispatcher"
    __DEVELOPMENT_JOB_DISPATCHER_TYPE = "_DevelopmentJobDispatcher"
    _scheduler: Optional[_Scheduler] = None
    _dispatcher: Optional[_JobDispatcher] = None

    @classmethod
    def _build_scheduler(cls) -> Type[_AbstractScheduler]:
        if util.find_spec(cls._TAIPY_ENTERPRISE_MODULE) is not None:
            cls._scheduler = _load_fct(
                cls._TAIPY_ENTERPRISE_CORE_SCHEDULER_MODULE,
                "Scheduler",
            )  # type: ignore
        else:
            cls._scheduler = _Scheduler  # type: ignore

        cls._scheduler.initialize()  # type: ignore

        return cls._scheduler  # type: ignore

    @classmethod
    def _build_dispatcher(cls, force_restart=False) -> Optional[_JobDispatcher]:
        if not cls._scheduler:
            raise SchedulerNotBuilt
        if Config.job_config.is_standalone:
            return cls.__build_standalone_job_dispatcher(force_restart=force_restart)
        elif Config.job_config.is_development:
            return cls.__build_development_job_dispatcher()
        else:
            raise ModeNotAvailable(f"Job mode {Config.job_config.mode} is not available.")

    @classmethod
    def __build_standalone_job_dispatcher(cls, force_restart=False) -> Optional[_JobDispatcher]:
        if isinstance(cls._dispatcher, _StandaloneJobDispatcher) and not isinstance(
            cls._dispatcher, _DevelopmentJobDispatcher
        ):
            if force_restart:
                cls._dispatcher.stop()
            else:
                return None
        cls._dispatcher = cls.__build_dispatcher(cls.__STANDADLONE_JOB_DISPATCHER_TYPE)
        cls._dispatcher.start()  # type: ignore
        return cls._dispatcher

    @classmethod
    def __build_development_job_dispatcher(cls) -> _JobDispatcher:
        if isinstance(cls._dispatcher, _StandaloneJobDispatcher) and not isinstance(
            cls._dispatcher, _DevelopmentJobDispatcher
        ):
            cls._dispatcher.stop()
        cls._dispatcher = cls.__build_dispatcher(cls.__DEVELOPMENT_JOB_DISPATCHER_TYPE)
        return cls._dispatcher

    @classmethod
    def __build_dispatcher(cls, dispatcher_type: str) -> _JobDispatcher:
        print("build a dispatcher enterprise or core")
        if util.find_spec(cls._TAIPY_ENTERPRISE_MODULE) is not None:
            return _load_fct(
                cls._TAIPY_ENTERPRISE_CORE_DISPATCHER_MODULE,
                dispatcher_type,
            )(cls._scheduler)
        if dispatcher_type == "_DevelopmentJobDispatcher":
            return _DevelopmentJobDispatcher(cls._scheduler)  # type: ignore
        else:
            return _StandaloneJobDispatcher(cls._scheduler)  # type: ignore
