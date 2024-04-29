CREATE TABLE public.shading_monthly (
    tree_id TEXT REFERENCES public.trees(id),
    january REAL,
    february REAL,
    march REAL,
    april REAL,
    may REAL,
    june REAL,
    july REAL,
    august REAL,
    september REAL,
    october REAL,
    november REAL,
    december REAL,
    PRIMARY KEY(tree_id)
);