import { AffectableTargetCreature } from './AffectableTarget';
export declare class AffectableTargetCreatureFake extends AffectableTargetCreature {
    resisted: boolean;
    receiveDamage: import("vitest").Mock<any, any>;
    setCondition: import("vitest").Mock<any, any>;
    resist(): boolean;
}
