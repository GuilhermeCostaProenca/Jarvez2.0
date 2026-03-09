import type { AffectableTargetCreature } from '../Affectable/AffectableTarget';
import type { DamageType } from '../Damage/DamageType';
import type { SkillName } from '../Skill/SkillName';
export declare class HalfResistanceDamageApplier {
    readonly maxDamage: number;
    readonly difficulty: number;
    readonly damageType: DamageType;
    readonly resistSkill: SkillName;
    constructor(maxDamage: number, difficulty: number, damageType: DamageType, resistSkill: SkillName);
    apply(creature: AffectableTargetCreature): void;
}
