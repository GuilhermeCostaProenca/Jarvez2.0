import type { Affectable, AffectableType } from '../Affectable/Affectable';
import type { AreaFormat } from '../Affectable/AffectableArea';
import type { TargetType } from '../Affectable/AffectableTarget';
export declare class EffectAffectable implements Affectable {
    readonly affectableType: AffectableType;
    constructor(affectableType: AffectableType);
}
export declare class EffectAffectableArea extends EffectAffectable {
    readonly format: AreaFormat;
    constructor(format: AreaFormat);
}
export declare class EffectAffectableTarget extends EffectAffectable {
    readonly targetType: TargetType;
    readonly quantity: number;
    constructor(targetType: TargetType, quantity: number);
}
