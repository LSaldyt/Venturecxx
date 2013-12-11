def normalizeList(seq): 
  denom = sum(seq)
  return [ float(x)/denom for x in seq]

def sampleCategoricalIter(x,index,psSoFar,psRemaining):
  if x < psSoFar: return index
  if not psRemaining: return index
  else: return sampleCategoricalIter(x,index+1,psSoFar + psRemaining[0],psRemaining[1:])

def sampleCategorical(ps):
  x = random.random()
  index = sampleCategoricalIter(x,0,ps[0],ps[1:])
  assert index < len(ps)
  return index
