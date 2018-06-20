from __future__ import absolute_import

import socket

from . import MetricsAgent
from ...common.db import DB_API
from ...models.metrics.dp import Ceph_OSD


class CephOSD_Agent(MetricsAgent):
    measurement = 'ceph_osd'

    def _collect_data(self):
        # process data and save to 'self.data'
        obj_api = DB_API(self._ceph_context)
        perf_data = obj_api.get_all_perf_counters()
        if not perf_data and not isinstance(perf_data, dict):
            self._logger.error("unable to get all perf counters")
            return
        cluster_id = obj_api.get_cluster_id()
        for n_name, i_perf in perf_data.iteritems():
            if not n_name[0:3].lower() == 'osd':
                continue
            d_osd = Ceph_OSD()
            stat_bytes = 0
            stat_bytes_used = 0
            d_osd.tags['cluster_id'] = cluster_id
            d_osd.tags['osd_id'] = n_name[4:]
            d_osd.fields['agenthost'] = socket.gethostname()
            d_osd.tags['agenthost_domain_id'] = \
                '%s_%s' % (cluster_id, d_osd.fields['agenthost'])
            d_osd.tags['host_domain_id'] = \
                '%s_%s' % (cluster_id,
                           obj_api.get_osd_hostname(d_osd.tags['osd_id']))
            for i_key, i_val in i_perf.iteritems():
                if i_key[:4] == 'osd.':
                    key_name = i_key[4:]
                else:
                    key_name = i_key
                d_osd.fields[key_name] = i_val.get('value', 0)
                if key_name == 'stat_bytes':
                    stat_bytes = i_val.get('value', 0)
                if key_name == 'stat_bytes_used':
                    stat_bytes_used = i_val.get('value', 0)
            if stat_bytes and stat_bytes_used:
                d_osd.fields['stat_bytes_used_percentage'] = \
                    round(float(stat_bytes_used) / float(stat_bytes) * 100, 4)
            else:
                d_osd.fields['stat_bytes_used_percentage'] = 0.0000
            self.data.append(d_osd)
