import { type Attribute } from '../../../../Sheet';
import { type SkillName } from '../../../../Skill';
export type WeaponPurposeParams = {
    penalty?: number;
    customTestAttributes?: Set<Attribute>;
    damageAttribute?: Attribute;
    defaultSkill: SkillName;
};
export declare abstract class WeaponPurpose {
    readonly penalty: number;
    readonly customTestAttributes: Set<Attribute>;
    readonly damageAttribute: Attribute | undefined;
    readonly defaultSkill: SkillName;
    constructor(params: WeaponPurposeParams);
}
