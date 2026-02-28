import type { Affectable, AffectableType } from './Affectable';
import type { AffectableTargetCreature } from './AffectableTarget';
export type AreaFormat = 'square' | 'circle' | 'cone';
export type AffectableAreaInterface = Affectable & {
    format: AreaFormat;
    getCreaturesInside(): AffectableTargetCreature[];
};
export declare abstract class AffectableArea implements AffectableAreaInterface {
    readonly format: AreaFormat;
    affectableType: AffectableType;
    constructor(format: AreaFormat);
    abstract getCreaturesInside(): AffectableTargetCreature[];
}
