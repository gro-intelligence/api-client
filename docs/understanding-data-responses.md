# Understanding Data Responses

## Look up
If it is ever unclear what an id number represents, you can use `lookup` to get all the information you'd need. `lookup` works for any of the [data series selection entities](./data-series-definition): `items`, `metrics`, `regions`, `frequencies`, `sources` and also `units`. For example:
```client.lookup('frequencies','7')```
returns:
```{'abbrev': None, 'id': 7, 'name': 'quarterly', 'periodLength': {'months': 3}}```

```client.lookup('metrics','1480032')```
returns:
```py
{'allowNegative': False,
 'allowedAggregations': '{sum,average}',
 'contains': [],
 'definition': 'The quantity of an item which has been consumed within a given country or region. Data generally refers to consumption as including any form of disappearance, such as waste, loss, and human consumption.',
 'id': 1480032,
 'name': 'Domestic Consumption (mass)'}
 ```
 
```client.lookup('units', '10')```
returns:
```py
{'abbreviation': 'kg',
 'baseConvFactor': {'factor': 1},
 'convType': 0,
 'id': 10,
 'name': 'kilogram',
 'namePlural': 'kilograms'}
 ```
 
You can also get this information by going to the URL of the dictionary entry for individual entities in the Gro ontology, e.g. <https://app.gro-intelligence.com/#/dictionary/items/270> or <https://app.gro-intelligence.com/#/dictionary/regions/1309>.
