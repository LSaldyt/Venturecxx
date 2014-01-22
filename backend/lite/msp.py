from psp import PSP, ESRRefOutputPSP
from sp import SP
from env import Env
from request import Request,ESR


class MakeMSPOutputPSP(PSP):
  def simulate(self,args):
    sharedOperatorNode = args.operandNodes[0]
    return SP(MSPRequestPSP(sharedOperatorNode),ESRRefOutputPSP())

class MSPRequestPSP(PSP):
  def __init__(self,sharedOperatorNode): self.sharedOperatorNode = sharedOperatorNode
  def simulate(self,args): 
    id = str(args.operandValues)
    exp = ["memoizedSP"] + [["quote"] + args.operandValues] if args.operandValues else ["memoizedSP"]
    env = Env(None,["memoizedSP"],[self.sharedOperatorNode])
    return Request([ESR(id,exp,env)])
