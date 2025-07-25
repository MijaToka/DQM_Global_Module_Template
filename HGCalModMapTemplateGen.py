#import FWCore.ParameterSet.Config as cms
from ROOT import TFile,TTree,TGraph,TH2Poly
import argparse
import pandas as pd
import numpy as np
import os

# u,v ID and rotation functions from hgcal_modmap/utils/make_CMSSW_flatfile.py
def fullRot(tx, ty, angle):

    """ rotation in the transverse plane by arbitrary angle """

    cangle = np.cos(angle)
    sangle = np.sin(angle)
    xx = tx*cangle - ty *sangle
    yy = tx*sangle +ty*cangle
    newcor = [xx,yy]
    return (newcor)


def modId(iplane,xc,yc):

    """return module id (u,v) coordinates, starting from the position in a plane"""

    iuv = [99,99]
    w = 167.4408
    sq3 = 1.73205
    f = -1.
    if iplane <= 33:  # attention numbering from 1, odd/even changed
        off = 0.
    if iplane > 33 and iplane % 2 == 1:
        off = w / sq3
    if iplane > 33 and iplane % 2 == 0:
        off = -w / sq3

    u = (yc - off) / (w * sq3) - f * xc / w
    if u > -0.5:
        iu = int(u + 0.01)
    else:
        iu = int(u - 0.01)

    v = 2. * (yc - off) / (w * sq3)
    if v > -0.5:
        iv = int(v + 0.01)
    else:
        iv = int(v - 0.01)

    iuv=[iu,iv]
    return (iuv)

def parse_arguments():
    parser = argparse.ArgumentParser(description="Process some arguments.")

    parser.add_argument('--version',type=str, 
        default='16.5', help='Which version of the Module maper are you using. Default: 16.5')
    
    parser.add_argument('--layer_preview',action="store_true",
        help="Enables saving a layer-by-layer preview of the modules")

    return parser.parse_args()

def main(args):

    cwd = os.getcwd()
    in_dir = os.path.join(cwd,"Geometry","v"+args.version,"geometry."+args.version+".txt")
    print(f"Input file: {in_dir}")

    out_dir = os.path.join(cwd, "output","v"+args.version)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir,exist_ok=True)
    out_dir = os.path.join(out_dir,"geometry_v"+args.version+".root")
    
    print(f"Output directory: {out_dir}")
    ## Open the ModMap file and the output file
    cols = ['plane', 'u', 'v', 'isSiPM', 'x0', 'y0',
        'nvertices', 'vx_0', 'vy_0', 'vx_1', 'vy_1', 'vx_2', 'vy_2', 'vx_3',
        'vy_3', 'vx_4', 'vy_4', 'vx_5', 'vy_5', 'vx_6', 'vy_6', 'icassette']

    modMap = pd.read_csv(in_dir,sep=' ')

    if not (in_file_full_modmap := False):
        print('Generating other 2 sectors.')
        new_sectors = pd.DataFrame(columns=cols)

        for row in modMap.itertuples():
            
            #sanity check
            x0,y0=row.x0,row.y0
            if row.plane<=26 and row.plane%2==0: x0=-x0
            if not row.isSiPM:
                uv = modId(row.plane,x0,y0)
                assert(uv[0]==row.u and uv[1]==row.v),(uv,[row.u,row.v],row.isSiPM,row.plane)


            for jrot in range(1,3):
                
                angle = (2.*np.pi/3)*jrot
                sign = 1 if row.plane % 2 == 1 else -1

                rot_xy0 = fullRot(x0,y0,angle) # This is flipped so it doesn't need the sign in the rotation
                rot_vxy_i = []

                for i in range(7):
                    rot_vxy_i += fullRot( getattr(row,f'vx_{i}'), getattr(row,f'vy_{i}'), sign * angle )

                if row.isSiPM:
                    rot_uv = [row.u,row.v+12*jrot]
                else:
                    rot_uv = modId(row.plane,rot_xy0[0],rot_xy0[1])

                if row.plane > 26:  rot_icassette = row.icassette + 4*jrot
                else:               rot_icassette = row.icassette + 2*jrot

                new_row = [row.plane,*rot_uv,row.isSiPM, sign * rot_xy0[0],rot_xy0[1],row.nvertices,*rot_vxy_i,rot_icassette]
                new_sectors = pd.concat([new_sectors,pd.DataFrame([new_row],columns=cols)],ignore_index=True)
        modMap = pd.concat([modMap,new_sectors],ignore_index=True)
        modMap = modMap.sort_values(['plane','u','v'])
        modMap.reset_index()    


    print('Writing the into the ROOT File.')
    fout = TFile(out_dir,"RECREATE")
    layer_polys = [TH2Poly() for _ in range(47)]
    #Fill the root file
    for module in modMap.itertuples():
        fout.cd('/')
        module_path = f"isSiPM_{module.isSiPM}/plane_{module.plane}/u_{module.u}/v_{module.v}"
        if not fout.GetDirectory(module_path):
            fout.mkdir(module_path)
        else: print(module_path + " accessed again!")
        fout.cd(f"/{module_path}")

        x = np.array([getattr(module,"vx_{}".format(i)) for i in range(7)],dtype=float)/10
        y = np.array([getattr(module,"vy_{}".format(i)) for i in range(7)],dtype=float)/10
        
        graph = TGraph(module.nvertices+1, x, y)
        graph.SetTitle("")
        graph.SetName("module_bin")
        graph.GetXaxis().SetTitle("x [cm]")
        graph.GetYaxis().SetTitle("y [cm]")

        x0 = np.zeros(1,dtype=float)
        y0 = np.zeros(1,dtype=float)
        icassette = np.zeros(1,dtype=int)
        
        tree = TTree("module_properties","Module properties x0,y0,icassette")
        tree.Branch('x0',x0,'x0/D')
        tree.Branch('y0',y0,'y0/D')
        tree.Branch('icassette',icassette,'icassette/I')

        x0[0] = module.x0/10 #Modmap is in [mm] and the wafer maps are in [cm]
        y0[0] = module.y0/10
        icassette[0] = module.icassette

        tree.Fill()
        #center_position = ROOT.TVector2(module.x0/10,module.y0/10)

        graph.Write()
        graph.SetName(f"Module_({module.u},{module.v})")
        layer_polys[int(module.plane) - 1].AddBin(graph)
        tree.Write()
        #center_position.Write("module_x0y0")
        tree.SetDirectory(0)  # Detach so it's not written again
        del tree  # Cleanup reference
    if args.layer_preview:
        fout.cd("/")
        fout.mkdir("Layers")
        fout.cd("/Layers")
        for plane in range(1,48):
            layer_polys[plane-1].SetName(f"Layer_{plane}")
            layer_polys[plane-1].SetTitle(f"Layer_{plane}")
            layer_polys[plane-1].Write()

    fout.Write()
    fout.Close()

if __name__ == '__main__':
    args = parse_arguments()
    print(f"ModMap version: {args.version}")
    main(args)