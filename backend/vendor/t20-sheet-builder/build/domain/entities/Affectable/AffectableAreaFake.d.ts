import { AffectableArea } from './AffectableArea';
import { AffectableTargetCreatureFake } from './AffectableTargetCreatureFake';
export declare class AffectableAreaFake extends AffectableArea {
    creaturesInside: AffectableTargetCreatureFake[];
    constructor();
    getCreaturesInside(): AffectableTargetCreatureFake[];
}
