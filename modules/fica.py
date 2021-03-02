# -*- coding: utf-8 -*-
"""module for carving."""
from modules import manager
from modules import interface

from modules.FICA import main as fica

class Fica(interface.ModuleConnector):
    NAME = 'fica_connector'
    DESCRIPTION = 'Module for file carving'

    def __init__(self):
        super(Fica, self).__init__()

    def Connect(self, configuration, knowledge_base, source_path_spec=None, par_id=None):
        output_path = configuration.root_tmp_path
        if par_id and source_path_spec.TYPE_INDICATOR is not 'OS':
            query = f"SELECT sector_size, cluster_size, par_size, start_sector FROM partition_info WHERE par_id='{par_id}';"

            result = configuration.cursor.execute_query(query)
            if len(result) == 0:
                return False

            sector_size = result[0]
            cluster_size = result[1]
            par_size = result[2]
            start_sector = result[3]

            case_profile = {
                "name": par_id,
                "uid": configuration.case_id,
                "path": configuration.source_path,
                "out": output_path,
                "off_start": start_sector * sector_size,
                "off_end": start_sector * sector_size + par_size,
                "cluster": cluster_size,
                "sector": sector_size,
                "encode": "utf-8",
                "extract": True,
                "export": True
            }

        else:
            case_profile = {
                "name": configuration.case_id,
                "uid": configuration.case_id,
                "path": configuration.source_path,
                "out": output_path,
                "off_start": 0,
                "off_end": 0,
                "cluster": configuration.cluster_size,
                "sector": configuration.sector_size,
                "encode": "utf-8",
                "extract": True,
                "export": True
            }

        copier = fica.main(case_profile)

        try:
            if not isinstance(copier, int):
                copier.insert(0, 'case_id', configuration.case_id)
                copier.insert(1, 'evd_id', configuration.evidence_id)
                copier.insert(2, 'par_id', par_id)
                # Insert to DB
                if configuration.standalone_check:
                    copier.to_sql(name='carve', con=configuration.cursor._conn, if_exists='append', index=False)
                else:
                    engine = configuration.cursor.create_engine()
                    copier.to_sql(name='carve', con=engine, if_exists='append', index=False)
        except Exception as e:
            print("Carving failed")


manager.ModulesManager.RegisterModule(Fica)
