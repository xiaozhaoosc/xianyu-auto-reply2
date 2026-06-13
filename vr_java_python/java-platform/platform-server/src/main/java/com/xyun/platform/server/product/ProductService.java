package com.xyun.platform.server.product;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.xyun.platform.common.dto.ApiResult;
import com.xyun.platform.common.entity.XyCatalogItem;
import com.xyun.platform.common.entity.XyProductMaterial;
import com.xyun.platform.common.entity.XyPublishAddress;
import com.xyun.platform.common.exception.BusinessException;
import com.xyun.platform.server.mapper.XyCatalogItemMapper;
import com.xyun.platform.server.mapper.XyProductMaterialMapper;
import com.xyun.platform.server.mapper.XyPublishAddressMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

/**
 * 商品管理 Service — 商品目录、素材库、地址池 CRUD
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class ProductService {

    private final XyCatalogItemMapper catalogItemMapper;
    private final XyProductMaterialMapper productMaterialMapper;
    private final XyPublishAddressMapper publishAddressMapper;

    // ==================== 商品目录 ====================

    /**
     * 分页查询商品目录
     */
    public ApiResult<Page<XyCatalogItem>> listCatalogItems(int current, int size, Long accountId) {
        var page = new Page<XyCatalogItem>(current, size);
        var wrapper = new LambdaQueryWrapper<XyCatalogItem>()
                .eq(accountId != null, XyCatalogItem::getAccountId, accountId)
                .orderByDesc(XyCatalogItem::getCreatedAt);
        return ApiResult.ok(catalogItemMapper.selectPage(page, wrapper));
    }

    /**
     * 查询商品详情
     */
    public ApiResult<XyCatalogItem> getCatalogItem(Long id) {
        var item = catalogItemMapper.selectById(id);
        if (item == null) {
            throw new BusinessException("商品不存在: " + id);
        }
        return ApiResult.ok(item);
    }

    /**
     * 添加商品
     */
    public ApiResult<XyCatalogItem> addCatalogItem(XyCatalogItem item) {
        validateCatalogItem(item);
        catalogItemMapper.insert(item);
        return ApiResult.ok(item);
    }

    /**
     * 删除商品
     */
    public ApiResult<Void> deleteCatalogItem(Long id) {
        if (catalogItemMapper.deleteById(id) <= 0) {
            throw new BusinessException("商品不存在: " + id);
        }
        return ApiResult.ok();
    }

    // ==================== 素材库 ====================

    /**
     * 分页查询素材库
     */
    public ApiResult<Page<XyProductMaterial>> listProductMaterials(int current, int size, Long userId) {
        var page = new Page<XyProductMaterial>(current, size);
        var wrapper = new LambdaQueryWrapper<XyProductMaterial>()
                .eq(userId != null, XyProductMaterial::getUserId, userId)
                .orderByDesc(XyProductMaterial::getCreatedAt);
        return ApiResult.ok(productMaterialMapper.selectPage(page, wrapper));
    }

    /**
     * 创建素材
     */
    public ApiResult<XyProductMaterial> createProductMaterial(XyProductMaterial material) {
        validateProductMaterial(material);
        productMaterialMapper.insert(material);
        return ApiResult.ok(material);
    }

    /**
     * 更新素材
     */
    public ApiResult<XyProductMaterial> updateProductMaterial(Long id, XyProductMaterial material) {
        if (productMaterialMapper.selectById(id) == null) {
            throw new BusinessException("素材不存在: " + id);
        }
        material.setId(id);
        productMaterialMapper.updateById(material);
        return ApiResult.ok(material);
    }

    /**
     * 删除素材
     */
    public ApiResult<Void> deleteProductMaterial(Long id) {
        if (productMaterialMapper.deleteById(id) <= 0) {
            throw new BusinessException("素材不存在: " + id);
        }
        return ApiResult.ok();
    }

    // ==================== 地址池 ====================

    /**
     * 分页查询地址池
     */
    public ApiResult<Page<XyPublishAddress>> listPublishAddresses(int current, int size, String accountId) {
        var page = new Page<XyPublishAddress>(current, size);
        var wrapper = new LambdaQueryWrapper<XyPublishAddress>()
                .eq(StringUtils.hasText(accountId), XyPublishAddress::getAccountId, accountId)
                .orderByAsc(XyPublishAddress::getSortOrder);
        return ApiResult.ok(publishAddressMapper.selectPage(page, wrapper));
    }

    /**
     * 添加地址
     */
    public ApiResult<XyPublishAddress> addPublishAddress(XyPublishAddress address) {
        validatePublishAddress(address);
        publishAddressMapper.insert(address);
        return ApiResult.ok(address);
    }

    /**
     * 更新地址
     */
    public ApiResult<XyPublishAddress> updatePublishAddress(Long id, XyPublishAddress address) {
        if (publishAddressMapper.selectById(id) == null) {
            throw new BusinessException("地址不存在: " + id);
        }
        address.setId(id);
        publishAddressMapper.updateById(address);
        return ApiResult.ok(address);
    }

    /**
     * 删除地址
     */
    public ApiResult<Void> deletePublishAddress(Long id) {
        if (publishAddressMapper.deleteById(id) <= 0) {
            throw new BusinessException("地址不存在: " + id);
        }
        return ApiResult.ok();
    }

    // ==================== 参数校验 ====================

    /** 校验商品目录项 */
    private void validateCatalogItem(XyCatalogItem item) {
        if (!StringUtils.hasText(item.getItemId())) {
            throw new BusinessException("商品ID不能为空");
        }
        if (!StringUtils.hasText(item.getTitle())) {
            throw new BusinessException("商品标题不能为空");
        }
    }

    /** 校验素材 */
    private void validateProductMaterial(XyProductMaterial material) {
        if (material.getUserId() == null) {
            throw new BusinessException("用户ID不能为空");
        }
        if (!StringUtils.hasText(material.getTitle())) {
            throw new BusinessException("素材标题不能为空");
        }
    }

    /** 校验地址 */
    private void validatePublishAddress(XyPublishAddress address) {
        if (!StringUtils.hasText(address.getName())) {
            throw new BusinessException("地址名称不能为空");
        }
    }
}
