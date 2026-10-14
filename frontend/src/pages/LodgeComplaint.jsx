import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { complaintService } from '../services/complaints';
import { aiService } from '../services/ai';
import { Loader } from '../components/Common/Loader';
import { Toast } from '../components/Common/Toast';
import { Modal } from '../components/Common/Modal';
import { Upload, Sparkles, MapPin, AlertTriangle } from 'lucide-react';
import './LodgeComplaint.css';

export const LodgeComplaint = () => {
  const [categoriesList, setCategoriesList] = useState([]);
  const [categoriesSchema, setCategoriesSchema] = useState({});
  const [selectedCategoryName, setSelectedCategoryName] = useState('');
  const [subcategory, setSubcategory] = useState('');
  
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [location, setLocation] = useState('');
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState('');

  // Smart classification dry-run state
  const [isClassifying, setIsClassifying] = useState(false);
  const [aiSuggestion, setAiSuggestion] = useState(null);

  const [loading, setLoading] = useState(false);
  const [catsLoading, setCatsLoading] = useState(true);
  const [toast, setToast] = useState({ show: false, message: '', type: 'success' });

  // Duplicate Warning Modal state
  const [showDuplicateModal, setShowDuplicateModal] = useState(false);
  const [duplicateTicket, setDuplicateTicket] = useState(null);

  const navigate = useNavigate();

  useEffect(() => {
    const fetchCatsAndSchema = async () => {
      try {
        // Fetch both category objects (IDs + names) and subcategory mappings with independent fallbacks
        const [catsRes, schemaRes] = await Promise.all([
          complaintService.getCategories().catch((err) => { console.error("Failed to load categories:", err); return null; }),
          complaintService.getCategoriesSchema().catch((err) => { console.error("Failed to load schema:", err); return null; })
        ]);
        
        if (catsRes && catsRes.success && catsRes.data) {
          setCategoriesList(catsRes.data);
          if (!selectedCategoryName && catsRes.data.length > 0) {
            setSelectedCategoryName(catsRes.data[0].name);
          }
        }

        if (schemaRes && schemaRes.success && schemaRes.data) {
          setCategoriesSchema(schemaRes.data);
          
          const firstCat = Object.keys(schemaRes.data)[0];
          if (firstCat) {
            setSelectedCategoryName(firstCat);
            const subList = schemaRes.data[firstCat];
            if (subList && subList.length > 0) {
              setSubcategory(subList[0]);
            }
          }
        }
      } catch (e) {
        setToast({ show: true, message: 'Failed to load grievance categories.', type: 'error' });
      } finally {
        setCatsLoading(false);
      }
    };
    fetchCatsAndSchema();
  }, []);

  const handleCategoryChange = (e) => {
    const catName = e.target.value;
    setSelectedCategoryName(catName);
    const subList = categoriesSchema[catName] || [];
    if (subList.length > 0) {
      setSubcategory(subList[0]);
    } else {
      setSubcategory('');
    }
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImageFile(file);
      setImagePreview(URL.createObjectURL(file));
    }
  };

  const triggerAIAnalysis = async () => {
    if (!description.trim()) {
      setToast({ show: true, message: 'Please describe your grievance first to run smart analysis.', type: 'error' });
      return;
    }
    
    setIsClassifying(true);
    setAiSuggestion(null);

    try {
      const res = await aiService.dryRunClassify(description);
      if (res.success) {
        setAiSuggestion(res.data);
        
        // Auto-select category matching the prediction if it matches keys
        const matchedCatName = Object.keys(categoriesSchema).find(
          name => name.toLowerCase() === res.data.category.toLowerCase()
        );
        if (matchedCatName) {
          setSelectedCategoryName(matchedCatName);
          const subList = categoriesSchema[matchedCatName] || [];
          // If subcategory is also returned, match or select it
          const matchedSub = subList.find(sub => sub.toLowerCase() === (res.data.subcategory || '').toLowerCase());
          if (matchedSub) {
            setSubcategory(matchedSub);
          } else if (subList.length > 0) {
            setSubcategory(subList[0]);
          }
        }
      }
    } catch (e) {
      setToast({ show: true, message: 'Analysis failed. Falling back to manual choices.', type: 'error' });
    } finally {
      setIsClassifying(false);
    }
  };

  const handleSubmit = async (e, force = false) => {
    if (e) e.preventDefault();

    if (!title.trim() || !description.trim() || !selectedCategoryName || !location.trim()) {
      setToast({ show: true, message: 'Please fill in all required fields.', type: 'error' });
      return;
    }

    // Resolve category name to ID
    let categoryObj = categoriesList.find(c => c.name.toLowerCase() === selectedCategoryName.toLowerCase()) || categoriesList[0];
    if (!categoryObj) {
      try {
        const catRes = await complaintService.getCategories();
        if (catRes && catRes.success && catRes.data && catRes.data.length > 0) {
          setCategoriesList(catRes.data);
          categoryObj = catRes.data.find(c => c.name.toLowerCase() === selectedCategoryName.toLowerCase()) || catRes.data[0];
        }
      } catch (err) {
        console.error("Dynamic category recovery failed:", err);
      }
    }

    if (!categoryObj) {
      setToast({ show: true, message: 'Invalid category selection. Please select a valid grievance category.', type: 'error' });
      return;
    }

    setLoading(true);

    const formData = new FormData();
    formData.append('title', title.trim());
    formData.append('description', description.trim());
    formData.append('category_id', categoryObj.id.toString());
    formData.append('subcategory', subcategory);
    formData.append('location', location.trim());
    if (imageFile) {
      formData.append('image', imageFile);
    }

    try {
      const res = await complaintService.createComplaint(formData, force);
      if (res.success) {
        setToast({ show: true, message: 'Grievance submitted successfully!', type: 'success' });
        setShowDuplicateModal(false);
        setTimeout(() => {
          navigate('/student-dashboard');
        }, 1500);
      }
    } catch (error) {
      if (error.response?.status === 409 && error.response?.data?.error === 'duplicate_detected') {
        // Intercept duplicate warning and trigger modal popup
        setDuplicateTicket(error.response.data.duplicate);
        setShowDuplicateModal(true);
      } else {
        setToast({ 
          show: true, 
          message: error.response?.data?.message || 'Failed to submit grievance. Try again.', 
          type: 'error' 
        });
      }
    } finally {
      setLoading(false);
    }
  };

  if (catsLoading) {
    return <Loader message="Initializing grievance desk..." />;
  }

  return (
    <div className="lodge-complaint-container animate-fade-in">
      <div className="lodge-header-section">
        <h1>Raise a Grievance</h1>
        <p>Submit a new grievance ticket to the NBKR Grievance Desk. The system will analyze, route, and assign a resolution deadline.</p>
      </div>

      <div className="lodge-grid">
        <div className="lodge-form-card glass-card">
          <form onSubmit={(e) => handleSubmit(e, false)} className="lodge-form">
            <div className="form-group">
              <label htmlFor="title">Grievance Summary / Subject</label>
              <input
                id="title"
                type="text"
                className="form-input"
                placeholder="e.g. Water leak from washroom tap"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <div className="desc-label-row">
                <label htmlFor="description">Detailed Description</label>
                <button 
                  type="button" 
                  onClick={triggerAIAnalysis} 
                  className="btn btn-secondary ai-btn"
                  disabled={isClassifying}
                >
                  <Sparkles size={16} className="sparkle-icon" />
                  {isClassifying ? 'Analyzing...' : 'Auto-Suggest Details'}
                </button>
              </div>
              <textarea
                id="description"
                className="form-input text-area"
                rows={5}
                placeholder="Describe the grievance in detail. E.g. The third faucet in the block B washroom is leaking heavily. Water is pooling and causing a slippery hazard."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                required
              />
            </div>

            <div className="lodge-three-col">
              <div className="form-group">
                <label htmlFor="category">Grievance Category</label>
                <select
                  id="category"
                  className="form-input"
                  value={selectedCategoryName}
                  onChange={handleCategoryChange}
                  required
                >
                  {Object.keys(categoriesSchema).map((catName) => (
                    <option key={catName} value={catName}>
                      {catName}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="subcategory">Subcategory</label>
                <select
                  id="subcategory"
                  className="form-input"
                  value={subcategory}
                  onChange={(e) => setSubcategory(e.target.value)}
                  required
                >
                  {(categoriesSchema[selectedCategoryName] || []).map((subName) => (
                    <option key={subName} value={subName}>
                      {subName}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="location">Exact Location</label>
                <div className="location-input-wrapper">
                  <MapPin className="input-icon" size={16} />
                  <input
                    id="location"
                    type="text"
                    className="form-input has-icon"
                    placeholder="e.g. Hostel Block B, Room 204"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    required
                  />
                </div>
              </div>
            </div>

            <div className="form-group">
              <label>Upload Attachment (Optional)</label>
              <div className="upload-zone-wrapper">
                <label className="upload-zone">
                  <input 
                    type="file" 
                    accept="image/*" 
                    onChange={handleImageChange} 
                    className="hidden-file-input" 
                  />
                  <Upload className="upload-icon" size={24} />
                  <span>{imageFile ? 'Replace Photo' : 'Attach Image'}</span>
                  <span className="file-hint">PNG, JPG, JPEG (Max 16MB)</span>
                </label>
                
                {imagePreview && (
                  <div className="image-preview-box">
                    <img src={imagePreview} alt="Upload preview" />
                    <button 
                      type="button" 
                      onClick={() => { setImageFile(null); setImagePreview(''); }}
                      className="remove-preview-btn"
                    >
                      Remove
                    </button>
                  </div>
                )}
              </div>
            </div>

            <button type="submit" className="btn btn-primary submit-ticket-btn" disabled={loading}>
              {loading ? <Loader size="small" /> : 'Submit Grievance Ticket'}
            </button>
          </form>
        </div>

        {/* Recommendations Sidebar Panel */}
        <div className="lodge-ai-panel">
          <div className="glass-card ai-preview-card">
            <div className="ai-card-header">
              <Sparkles size={20} className="header-sparkle" />
              <h3>System Recommendations</h3>
            </div>
            
            {!aiSuggestion ? (
              <div className="ai-empty-state">
                <p>Click <strong>"Auto-Suggest Details"</strong> to automatically analyze your description. The system will recommend a category, subcategory, priority urgency level, and routing department.</p>
              </div>
            ) : (
              <div className="ai-results-content">
                <div className="ai-result-row">
                  <span className="ai-label">Predicted Category</span>
                  <span className="ai-val-badge badge-submitted">{aiSuggestion.category}</span>
                </div>

                <div className="ai-result-row">
                  <span className="ai-label">Recommended Subcategory</span>
                  <span className="ai-val-badge badge-review">{aiSuggestion.subcategory || 'General'}</span>
                </div>

                <div className="ai-result-row">
                  <span className="ai-label">Priority Level</span>
                  <span className={`ai-val-badge badge-${aiSuggestion.priority.toLowerCase()}`}>
                    {aiSuggestion.priority}
                  </span>
                </div>

                <div className="ai-result-row">
                  <span className="ai-label">Suggested Department</span>
                  <span className="ai-text-val">{aiSuggestion.department}</span>
                </div>

                <div className="ai-result-row">
                  <span className="ai-label">Confidence Rating</span>
                  <div className="confidence-progress-bar">
                    <div 
                      className="progress-fill" 
                      style={{ width: `${aiSuggestion.confidence * 100}%` }}
                    ></div>
                    <span className="progress-text">{(aiSuggestion.confidence * 100).toFixed(0)}%</span>
                  </div>
                </div>

                <div className="ai-disclaimer">
                  <p>Our smart system automatically organizes and routes tickets. You can still modify the selections manually if needed.</p>
                </div>

                <div style={{ marginTop: '16px', paddingTop: '12px', borderTop: '1px solid var(--border-color)', textAlign: 'center', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  Made by <strong style={{ color: 'var(--color-primary)' }}>BALAJI NAGELLA</strong>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Duplicate Warning Modal Dialog */}
      {duplicateTicket && (
        <Modal 
          isOpen={showDuplicateModal} 
          title="Similar Grievance Already Exists" 
          onClose={() => setShowDuplicateModal(false)}
        >
          <div className="duplicate-modal-content">
            <div className="duplicate-warning-header">
              <AlertTriangle className="warning-icon" size={32} />
              <p>You have already submitted a similar open ticket recently. Please review it to avoid creating duplicate requests.</p>
            </div>
            
            <div className="duplicate-ticket-summary">
              <div className="dup-field">
                <strong>Grievance ID:</strong> <span className="ticket-id-tag">{duplicateTicket.id}</span>
              </div>
              <div className="dup-field">
                <strong>Subject:</strong> {duplicateTicket.title}
              </div>
              <div className="dup-field">
                <strong>Current Status:</strong> <span className={`status-badge ${duplicateTicket.status.toLowerCase().replace(" ", "-")}`}>{duplicateTicket.status}</span>
              </div>
              <div className="dup-field">
                <strong>Submitted On:</strong> {new Date(duplicateTicket.created_at).toLocaleString()}
              </div>
            </div>

            <div className="duplicate-actions-row">
              <Link 
                to={`/complaint/${duplicateTicket.id}`} 
                target="_blank" 
                className="btn btn-secondary view-dup-btn"
              >
                View Existing Grievance
              </Link>
              <div className="dup-decision-btns">
                <button 
                  type="button" 
                  onClick={() => setShowDuplicateModal(false)} 
                  className="btn btn-outline"
                >
                  Cancel
                </button>
                <button 
                  type="button" 
                  onClick={() => handleSubmit(null, true)} 
                  className="btn btn-primary force-btn"
                  disabled={loading}
                >
                  {loading ? 'Submitting...' : 'Continue Submitting'}
                </button>
              </div>
            </div>
          </div>
        </Modal>
      )}

      {toast.show && (
        <Toast 
          message={toast.message} 
          type={toast.type} 
          onClose={() => setToast({ ...toast, show: false })} 
        />
      )}
    </div>
  );
};
export default LodgeComplaint;
