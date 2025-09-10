            select  b.name  as "table_name",  count(*)  as "count",  b.description  as
            "description",  b.regime  as "regime",  b.mission  as "mission",  b.type
            as "obj_type"
            from master_table.pos_small as a,master_table.indexview as b
            where  (  (  a.table_name  =  b.name  )  ) and  
            ( (a.__x_ra_dec*-0.12660100075964426 + a.__y_ra_dec*-0.9913070142170528 + a.__z_ra_dec*0.03581326808221165 > (cos(radians((a.dsr*60/60))))) 
            and (a.dec between 2.052388 - a.dsr*60/60 and 2.052388 + a.dsr*60/60)
            and (a.__x_ra_dec*-0.12660100075964426 + a.__y_ra_dec*-0.9913070142170528 + a.__z_ra_dec*0.03581326808221165 > 0.9998476951563913)
            and (a.dec between 1.052388 and 3.052388)
            )
            
            group by  b.name , b.description , b.regime , b.mission , b.type

            union all

            select  b.name  as "table_name",  count(*)  as "count",  b.description  as
            "description",  b.regime  as "regime",  b.mission  as "mission",  b.type
            as "obj_type"
            from master_table.pos_big as a,master_table.indexview as b
            where  (  (  a.table_name  =  b.name  )  ) and  
            ( (a.__x_ra_dec*-0.12660100075964426 + a.__y_ra_dec*-0.9913070142170528 + a.__z_ra_dec*0.03581326808221165 > (cos(radians((a.dsr*60/60))))) 
            and (a.dec between 2.052388 - a.dsr*60/60 and 2.052388 + a.dsr*60/60) ) 
            
            group by  b.name , b.description , b.regime , b.mission , b.type
            order by count desc