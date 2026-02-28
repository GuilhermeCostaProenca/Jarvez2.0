import { type SkillName } from '../../Skill';
import { type OriginPower } from './OriginPower';
import { OriginPowerName } from './OriginPowerName';
type OriginPowerFactoryParams = {
    power: OriginPowerName;
    specialFriendSkill?: SkillName;
};
export declare class OriginPowerFactory {
    static make(params: OriginPowerFactoryParams): OriginPower;
    private static readonly map;
}
export {};
