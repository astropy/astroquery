from dataclasses import dataclass
from typing import Tuple
import numpy as np

@dataclass
class UnitVectorDistance:
    @staticmethod
    def _get_vec(ra: str, dec: str) -> Tuple[str, str, str]:
        if 'a.' in ra:  # Assuming this indicates a column name
            prefix = ra.split('.')[0]  # e.g., 'a' from 'a.ra'
            return (f"{prefix}.__x_ra_dec", f"{prefix}.__y_ra_dec", f"{prefix}.__z_ra_dec")
        else:
            return UnitVectorDistance._compute_vec(float(ra), float(dec))

    @staticmethod
    def _compute_vec(ra: float, dec: float) -> Tuple[float, float, float]:
        r, d = np.radians([ra, dec])
        return (
            np.cos(d) * np.sin(r),
            np.cos(d) * np.cos(r),
            np.sin(d)
        )

    @staticmethod
    def constraint(ra: str, dec: str) -> str:
        vec0 = UnitVectorDistance._get_vec("a.ra", "a.dec")  # Assuming 'a' is the table alias
        vec1 = UnitVectorDistance._get_vec(ra, dec)
        dot_product = " + ".join([f"{vec0[i]}*{vec1[i]}" for i in range(3)])
        radius_condition = f"{dot_product} > (cos(radians((a.dsr*60/60))))"  # Assuming 'a.dsr' is the radius column
        dec_condition = f"a.dec between {dec} - a.dsr*60/60 and {dec} + a.dsr*60/60"
        vec_condition = f"{dot_product} > {vec0[2]}*{vec1[2]} and (a.dec between x and y)"
        
        return f"(({radius_condition}) and ({dec_condition}) and ({vec_condition}))"

def query_sql(ra: str, dec: str) -> str:
    constraint = UnitVectorDistance.constraint("187.277915", "2.052388")
    return(f"""
            select  b.name  as "table_name",  count(*)  as "count",  b.description  as
            "description",  b.regime  as "regime",  b.mission  as "mission",  b.type
            as "obj_type"
            from master_table.pos_small as a,master_table.indexview as b
            where  (  (  a.table_name  =  b.name  )  ) and  {constraint}
            group by  b.name , b.description , b.regime , b.mission , b.type

            union all

            select  b.name  as "table_name",  count(*)  as "count",  b.description  as
            "description",  b.regime  as "regime",  b.mission  as "mission",  b.type
            as "obj_type"
            from master_table.pos_big as a,master_table.indexview as b
            where  (  (  a.table_name  =  b.name  )  ) and  {constraint}
            group by  b.name , b.description , b.regime , b.mission , b.type
            order by count desc
            """)

            
# Example usage:
full_query = query_sql("187.277915", "2.052388")
print(full_query)
