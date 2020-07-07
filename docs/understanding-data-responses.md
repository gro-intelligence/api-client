# Understanding Data Responses

## Look up

If it is ever unclear what an id number represents, you can use `lookup` to get all the information you'd need. `lookup` works for any of the [data series selection entities](./data-series-definition): `items`, `metrics`, `regions`, `frequencies`, `sources` and also `units`. For example:

### Items

```py
client.lookup('items', 274)
```

returns:

```py
{ 'contains': [779, 780, 9338, 9339, 8219, 8220, 10568, 12431, 1443, 1687, 2749, 5433, 5128, 5127, 5125, 5001, 866, 867, 148, 692, 5126, 2175, 2514, 2515, 2516, 8092, 2521, 5114, 5118, 5115, 5116, 5117, 5601, 6338, 6586, 9252, 9253, 7626, 5103, 4370, 4368, 10106, 2303, 12697, 12698, 12699, 12700, 12701, 12702, 12703, 12704, 12705, 12706, 5434, 13479, 13652, 14725, 14726],
  'definition': "The seeds of the widely cultivated corn plant <i>Zea mays</i>, which is one of the world's most popular grains.",
  'id': 274,
  'name': 'Corn' }
 ```

### Frequencies

```py
client.lookup('frequencies', 7)
```

returns:

```py
{ 'abbrev': None,
  'id': 7,
  'name': 'quarterly',
  'periodLength': { 'months': 3 } }
```

### Units

```py
client.lookup('units', 10)
```

returns:

```py
{ 'abbreviation': 'kg',
  'baseConvFactor': { 'factor': 1 },
  'convType': 0,
  'id': 10,
  'name': 'kilogram',
  'namePlural': 'kilograms' }
 ```

You can also get this information by going to the URL of the dictionary entry for individual entities in the Gro ontology, e.g. <https://app.gro-intelligence.com/dictionary/items/270> or <https://app.gro-intelligence.com/dictionary/regions/1094>.
