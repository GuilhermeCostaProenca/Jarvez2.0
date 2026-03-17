import type { AffectableTargetCreature } from '../Affectable/AffectableTarget';
import type { Condition } from './Condition';
export declare class Stunned implements Condition {
    apply(affectable: AffectableTargetCreature): void;
}
